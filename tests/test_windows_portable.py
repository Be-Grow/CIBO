"""Testes Windows-portable — sem dependências pesadas."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"portable"))
from editorial import boundary_signals,add_feedback,feedback_summary,media_report

class PortableTests(unittest.TestCase):
    def test_detect_dangling_end(self):
        seg=[{"start":0,"end":10,"text":"Isso funciona quando"},
             {"start":10,"end":20,"text":"e você depende de"}]
        r=boundary_signals(seg,0,20)
        self.assertIn("dangling_last_word",r["signals"])
        self.assertEqual(r["status"],"review_required")

    def test_punctuation_is_not_semantic_approval(self):
        seg=[{"start":0,"end":10,"text":"Uma ideia que parece concluída."}]
        r=boundary_signals(seg,0,10)
        self.assertEqual(r["status"],"boundary_only_ok")
        self.assertIn("não comprovam",r["note"])

    def test_mid_sentence_flag(self):
        seg=[{"start":0,"end":5,"text":"Começo"},
             {"start":5,"end":12,"text":"Desenvolvimento."}]
        r=boundary_signals(seg,2,12)
        self.assertIn("start_inside_segment",r["signals"])

    def test_feedback_append_and_summary_local(self):
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/"feedback.jsonl"
            add_feedback(f,job_id="job1",source_sha256="a"*64,decision="rejected",
                         reason="ideia pendurada",start=5,end=20)
            add_feedback(f,job_id="job2",source_sha256="b"*64,decision="approved",
                         reason="completa")
            self.assertEqual(feedback_summary(f),{"approved":1,"rejected":1,"needs_review":0})
            with self.assertRaises(ValueError):
                add_feedback(f,job_id="job",source_sha256="INVALID",decision="approved",reason="invalid")

    def test_real_small_media_ffprobe(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"sample.mp4"
            try:subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","testsrc2=size=160x90:rate=8:duration=1",
                "-f","lavfi","-i","sine=frequency=400:duration=1",
                "-c:v","libx264","-threads","1","-preset","ultrafast",
                "-pix_fmt","yuv420p","-c:a","aac","-shortest",str(p)],
                check=True,capture_output=True,timeout=40)
            except FileNotFoundError:self.skipTest("ffmpeg não está disponível")
            r=media_report(p)
            self.assertTrue(r["decoder_ok"])
            self.assertEqual(len(r["sha256"]),64)
            self.assertIsNotNone(r["av_delta_seconds"])
            self.assertTrue(r["human_review_required"])

if __name__=="__main__":unittest.main()
