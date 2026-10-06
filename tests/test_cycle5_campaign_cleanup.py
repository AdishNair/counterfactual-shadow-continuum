"""Post-measurement orchestration regressions; no main study retries."""
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock,patch

from experiments import cycle5_async as campaign


class CampaignCleanupTests(unittest.TestCase):
    def row(self):
        return dict(mode='warm1',seed=1501,kind='factorial',condition='cpu',load='cpu',delay_s=0,run_id='cleanup-fixture')

    def test_ready_helper_death_always_stops_helper(self):
        proc=MagicMock(pid=12345);proc.poll.return_value=1
        with tempfile.TemporaryDirectory() as td,patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'did not become ready'):campaign.run_one(td,self.row())
            proc.wait.assert_called_once_with(timeout=10);run.assert_not_called()
            self.assertTrue((Path(td)/'pressure/cleanup-fixture/stop').exists())

    def test_readiness_timeout_always_stops_helper(self):
        proc=MagicMock(pid=12345);proc.poll.return_value=None
        with tempfile.TemporaryDirectory() as td,patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign.time,'perf_counter',side_effect=[0,11]),patch.object(campaign,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'did not become ready'):campaign.run_one(td,self.row())
            proc.wait.assert_called_once_with(timeout=10);run.assert_not_called()

    def test_stop_write_failure_still_terminates_and_kills(self):
        proc=MagicMock();proc.wait.side_effect=[subprocess.TimeoutExpired('helper',10),subprocess.TimeoutExpired('helper',2),0]
        with patch.object(Path,'write_text',side_effect=OSError('storage unavailable')):
            campaign.stop_pressure(proc,Path('unused-fixture'))
        proc.terminate.assert_called_once();proc.kill.assert_called_once()
        self.assertEqual([c.kwargs['timeout'] for c in proc.wait.call_args_list],[10,2,2])

    def test_stopping_unreapable_helper_fails_closed(self):
        proc=MagicMock();proc.wait.side_effect=subprocess.TimeoutExpired('helper',2)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError,'unconfirmed'):campaign.stop_pressure(proc,Path(td))
        proc.terminate.assert_called_once();proc.kill.assert_called_once()

    def test_campaign_watchdog_reaps_owned_tree_and_marks_timeout(self):
        proc=MagicMock(pid=12345,returncode=-9)
        proc.communicate.side_effect=[subprocess.TimeoutExpired('coordinator',700),('prefix','timeout')]
        with patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign.subprocess,'run') as terminate_tree,patch.object(campaign.os,'killpg',create=True) as kill_group:
            terminate_tree.return_value.returncode=0
            result,expired=campaign.execute_child(['fixture'],Path('.'),{},700)
        self.assertTrue(expired);self.assertEqual(result.stdout,'prefix')
        if campaign.os.name=='nt':
            self.assertEqual(terminate_tree.call_args.args[0],['taskkill','/PID','12345','/T','/F'])
        else:kill_group.assert_called_once()
        self.assertEqual(proc.communicate.call_args_list[-1].kwargs['timeout'],5)

    @unittest.skipUnless(campaign.os.name=='nt','Windows owned-tree cleanup')
    def test_tree_cleanup_failure_reaps_parent_then_fails_closed(self):
        proc=MagicMock(pid=12345,returncode=-9);proc.poll.return_value=None
        proc.communicate.side_effect=[subprocess.TimeoutExpired('coordinator',700),('prefix','timeout')]
        with patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign.subprocess,'run',side_effect=subprocess.TimeoutExpired('taskkill',10)):
            with self.assertRaisesRegex(RuntimeError,'campaign must stop'):
                campaign.execute_child(['fixture'],Path('.'),{},700)
        proc.kill.assert_called_once();self.assertEqual(proc.communicate.call_args_list[-1].kwargs['timeout'],5)

    def test_successful_child_has_bounded_wait_and_no_kill(self):
        proc=MagicMock(returncode=0);proc.communicate.return_value=('output','')
        with patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign.subprocess,'run') as terminate_tree:
            result,expired=campaign.execute_child(['fixture'],Path('.'),{},700)
        self.assertFalse(expired);self.assertEqual(result.returncode,0)
        proc.communicate.assert_called_once_with(timeout=700);terminate_tree.assert_not_called()

    def test_watchdog_is_control_not_deadline_extension(self):
        self.assertEqual(campaign.campaign_watchdog_s(self.row()),700)
        row=self.row();row.update(kind='long',condition='long-normal')
        self.assertEqual(campaign.campaign_watchdog_s(row),6300)
        self.assertEqual(campaign.configuration(row).shadow_result_deadline_s,.3)

    def test_termination_permission_error_still_attempts_kill_and_reap(self):
        proc=MagicMock();proc.wait.side_effect=[subprocess.TimeoutExpired('helper',10),subprocess.TimeoutExpired('helper',2),0]
        proc.terminate.side_effect=PermissionError('injected');proc.kill.side_effect=PermissionError('injected')
        with tempfile.TemporaryDirectory() as td:campaign.stop_pressure(proc,Path(td))
        proc.kill.assert_called_once();self.assertEqual(proc.wait.call_count,3)

    def test_uncertain_cleanup_aborts_next_condition_even_with_final_marker(self):
        rows=[self.row(),{**self.row(),'run_id':'forbidden-next'}]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);scratch=p/'pressure'/rows[0]['run_id'];scratch.mkdir(parents=True)
            (scratch/'final.json').write_text('{}')
            ownership=p/'ownership'/rows[0]['run_id'];ownership.mkdir(parents=True)
            (ownership/'cleanup.json').write_text('{"cleanup_confirmed":false}')
            result=subprocess.CompletedProcess([],1,'','cleanup uncertain')
            with patch.object(campaign,'prepare',return_value={'registry':rows}),patch.object(campaign,'execute_child',return_value=(result,False)) as launch,patch.object(campaign,'analyze',return_value={}):
                campaign.execute(p)
            self.assertEqual(launch.call_count,1)
            statuses=__import__('json').loads((p/'execution_status.json').read_text())
            self.assertFalse(statuses[0]['cleanup_confirmed']);self.assertEqual(statuses[1]['status'],'NOT_ATTEMPTED')

    def test_nonpressure_error_without_cleanup_aborts_next_condition(self):
        rows=[{**self.row(),'load':'normal'},{**self.row(),'run_id':'forbidden-next'}]
        with tempfile.TemporaryDirectory() as td,patch.object(campaign,'prepare',return_value={'registry':rows}),patch.object(campaign,'execute_child',side_effect=RuntimeError('cleanup permission denied')) as launch,patch.object(campaign,'analyze',return_value={}):
            campaign.execute(td)
            self.assertEqual(launch.call_count,1)
            statuses=__import__('json').loads((Path(td)/'execution_status.json').read_text())
            self.assertEqual(statuses[1]['status'],'NOT_ATTEMPTED')

    def test_non_timeout_communication_error_attempts_tree_cleanup_and_reap(self):
        proc=MagicMock(pid=12345,returncode=-9)
        proc.communicate.side_effect=[OSError('pipe failed'),('prefix','cleanup')]
        proc.poll.return_value=None
        with patch.object(campaign.subprocess,'Popen',return_value=proc),patch.object(campaign.subprocess,'run') as terminate_tree:
            terminate_tree.return_value.returncode=0
            with self.assertRaisesRegex(RuntimeError,'launcher error'):
                campaign.execute_child(['fixture'],Path('.'),{},700)
        terminate_tree.assert_called_once()
        proc.kill.assert_called_once()
        self.assertEqual(proc.communicate.call_count,2)

    def test_wrong_confirmation_json_shapes_follow_uncertain_abort_path(self):
        rows=[{**self.row(),'load':'normal'},{**self.row(),'run_id':'forbidden-next'}]
        for malformed in ('[]','null','"text"'):
            with self.subTest(malformed=malformed),tempfile.TemporaryDirectory() as td:
                root=Path(td);ownership=root/'ownership'/rows[0]['run_id'];ownership.mkdir(parents=True)
                (ownership/'cleanup.json').write_text(malformed)
                result=subprocess.CompletedProcess([],0,'','')
                with patch.object(campaign,'prepare',return_value={'registry':rows}),patch.object(campaign,'execute_child',return_value=(result,False)) as launch,patch.object(campaign,'analyze',return_value={}):
                    campaign.execute(root)
                self.assertEqual(launch.call_count,1)
                statuses=__import__('json').loads((root/'execution_status.json').read_text())
                self.assertFalse(statuses[0]['cleanup_confirmed'])
                self.assertEqual(statuses[0]['status'],'FAILED')
                self.assertEqual(statuses[1]['status'],'NOT_ATTEMPTED')

    def test_final_condition_uncertain_cleanup_cannot_report_complete_campaign(self):
        rows=[{**self.row(),'load':'normal'}]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ownership=root/'ownership'/rows[0]['run_id'];ownership.mkdir(parents=True)
            (ownership/'cleanup.json').write_text('null')
            result=subprocess.CompletedProcess([],0,'','')
            with patch.object(campaign,'prepare',return_value={'registry':rows}),patch.object(campaign,'execute_child',return_value=(result,False)),patch.object(campaign,'analyze',return_value={}):
                campaign.execute(root)
            statuses=__import__('json').loads((root/'execution_status.json').read_text())
            manifest=__import__('json').loads((root/'series_manifest.json').read_text())
            self.assertEqual(statuses[0]['status'],'FAILED')
            self.assertEqual(manifest['status'],'HAS_FAILED_OR_UNATTEMPTED_RUNS')

    def test_prepare_accepts_only_explicit_source_compatible_complete_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);gate_path=root/'gate.json';series=root/'series'
            required=[*sorted((campaign.ROOT/'csc').glob('*.py')),*sorted((campaign.ROOT/'tests').glob('*.py'))]
            required += [campaign.ROOT/name for name in ('experiments/__init__.py','experiments/cycle5_async.py',
                                                         'experiments/cycle5_pressure.py','experiments/cycle5_loss.py',
                                                         'experiments/replay.py')]
            hashes={str(path.relative_to(campaign.ROOT)).replace('\\','/'):campaign.sha256_file(path) for path in required}
            gate_path.write_text(__import__('json').dumps({'status':'COMPLETE','exit_code':0,
                                                          'source_hashes':hashes,'source_identity_sha256':'fixture'}))
            meta=campaign.prepare(series,gate_path)
            self.assertEqual(meta['correctness_gate_source_identity_sha256'],'fixture')
            self.assertTrue((series/'source/gates/readiness_manifest.json').is_file())
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError,'explicit compatible'):
                campaign.prepare(Path(td)/'series')

    def test_prepare_rechecks_copied_execution_source_against_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);gate_path=root/'gate.json';series=root/'series'
            required=[*sorted((campaign.ROOT/'csc').glob('*.py')),*sorted((campaign.ROOT/'tests').glob('*.py'))]
            required += [campaign.ROOT/name for name in ('experiments/__init__.py','experiments/cycle5_async.py',
                                                         'experiments/cycle5_pressure.py','experiments/cycle5_loss.py',
                                                         'experiments/replay.py')]
            hashes={str(path.relative_to(campaign.ROOT)).replace('\\','/'):campaign.sha256_file(path) for path in required}
            gate_path.write_text(__import__('json').dumps({'gate_passed':True,'exit_code':0,
                                                          'source_hashes':hashes,'source_identity_sha256':'fixture'}))
            original=campaign.shutil.copy2
            def changed_copy(source,target,*args,**kwargs):
                value=original(source,target,*args,**kwargs)
                if str(source).replace('\\','/').endswith('experiments/cycle5_pressure.py'):
                    Path(target).write_text('# changed between check and copy\n')
                return value
            with patch.object(campaign.shutil,'copy2',side_effect=changed_copy):
                with self.assertRaisesRegex(RuntimeError,'Copied execution source differs'):
                    campaign.prepare(series,gate_path)

    def test_analysis_excludes_cleanup_failed_complete_artifact(self):
        row=self.row()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'preregistration.json').write_text(__import__('json').dumps({'registry':[row]}))
            (root/'execution_status.json').write_text(__import__('json').dumps([
                {'run_id':row['run_id'],'status':'FAILED','cleanup_confirmed':False}]))
            reduced={**row,'status':'COMPLETE','complete_fraction':1,
                     'production_interval_ms':{'median':40},'branch_status_counts':{}}
            with patch.object(campaign,'reduce_run',return_value=reduced):
                report=campaign.analyze(root)
            self.assertFalse(report['groups'])
            self.assertEqual(len(report['failed_or_unattempted_runs']),1)
            failed=report['failed_or_unattempted_runs'][0]
            self.assertEqual(failed['status'],'FAILED_CONTROL_OR_CLEANUP')
            self.assertEqual(failed['artifact_status'],'COMPLETE')

    def test_real_child_uncertain_ownership_stops_launcher_boundary(self):
        rows=[self.row(),{**self.row(),'run_id':'forbidden-next'}]
        real_execute_child=campaign.execute_child
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            childcode="from pathlib import Path; import sys; root=Path(sys.argv[1]); o=root/'ownership'/'cleanup-fixture'; o.mkdir(parents=True); (o/'cleanup.json').write_text('{\"cleanup_confirmed\":false}'); f=root/'pressure'/'cleanup-fixture'; f.mkdir(parents=True); (f/'final.json').write_text('{}'); sys.exit(1)"
            def launch(*args,**kwargs):return real_execute_child([sys.executable,'-c',childcode,td],Path('.'),dict(campaign.os.environ),10)
            with patch.object(campaign,'prepare',return_value={'registry':rows}),patch.object(campaign,'execute_child',side_effect=launch) as launches,patch.object(campaign,'analyze',return_value={}):
                campaign.execute(p)
            self.assertEqual(launches.call_count,1)
            statuses=__import__('json').loads((p/'execution_status.json').read_text())
            self.assertFalse(statuses[0]['cleanup_confirmed']);self.assertEqual(statuses[1]['status'],'NOT_ATTEMPTED')

    @unittest.skipUnless(campaign.os.name=='nt','Real disposable Windows owned process tree')
    def test_real_windows_owned_tree_timeout_terminates_descendant(self):
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as td:
            pid_path=Path(td)/'descendant.pid'
            code="import subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(120)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); open(sys.argv[1],'w').write(str(child.pid)); time.sleep(120)"
            captured={}
            def launch():captured['value']=campaign.execute_child([sys.executable,'-c',code,str(pid_path)],Path('.'),dict(campaign.os.environ),2)
            thread=threading.Thread(target=launch);thread.start()
            deadline=time.monotonic()+1
            while not pid_path.exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue(pid_path.exists(),'Descendant PID was not published before cleanup')
            child_pid=int(pid_path.read_text())
            handle=kernel.OpenProcess(0x00100000,False,child_pid)
            self.assertTrue(handle,'Could not acquire descendant handle before cleanup')
            try:
                thread.join(10);self.assertFalse(thread.is_alive())
                result,expired=captured['value'];self.assertTrue(expired)
                self.assertEqual(kernel.WaitForSingleObject(handle,5000),0,'Owned descendant did not signal exit')
            finally:
                if thread.is_alive():subprocess.run(['taskkill','/PID',str(child_pid),'/T','/F'],capture_output=True,timeout=10)
                kernel.CloseHandle(handle)


if __name__=='__main__':unittest.main()
