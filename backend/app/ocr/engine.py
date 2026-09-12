import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class OCREngine:
    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.local_dir = self.project_root / "local_tesseract"
        self.local_bin = self.local_dir / "bin" / "tesseract"
        self.local_lib = self.local_dir / "lib"
        self.local_tessdata = self.local_dir / "tessdata"

        # Ensure LD_LIBRARY_PATH includes local bundled libraries if available
        if self.local_lib.exists():
            curr_ld = os.environ.get("LD_LIBRARY_PATH", "")
            if str(self.local_lib) not in curr_ld:
                os.environ["LD_LIBRARY_PATH"] = f"{self.local_lib}:{curr_ld}".rstrip(":")

        self.cmd = self._find_tesseract_cmd(tesseract_cmd)
        self.data_path = self._find_tessdata()
        self.available = self._check_available()

    def _find_tesseract_cmd(self, default_cmd: str) -> str:
        # 1. Check system path first
        sys_path = shutil.which(default_cmd)
        if sys_path:
            return sys_path
        # 2. Check local bundled tesseract
        if self.local_bin.exists():
            return str(self.local_bin)
        return default_cmd

    def _find_tessdata(self) -> Optional[str]:
        candidates = [
            os.environ.get("TESSDATA_PREFIX"),
            str(self.local_tessdata) if self.local_tessdata.exists() else None,
            "/usr/share/tesseract-ocr/5/tessdata",
            "/usr/share/tesseract-ocr/4.00/tessdata",
            "/usr/share/tessdata",
            "/usr/local/share/tessdata",
        ]
        for path in candidates:
            if path and Path(path).joinpath("eng.traineddata").exists():
                return path
        return None

    def _check_available(self) -> bool:
        # Check pytesseract + binary execution
        try:
            import pytesseract
            from PIL import Image

            pytesseract.pytesseract.tesseract_cmd = self.cmd
            test_img = Image.new("L", (20, 20), color=255)
            config = f'--tessdata-dir "{self.data_path}"' if self.data_path else ""
            pytesseract.image_to_string(test_img, config=config)
            return True
        except Exception:
            # Fallback check: can the tesseract binary execute --version?
            try:
                env = dict(os.environ)
                if self.local_lib.exists():
                    env["LD_LIBRARY_PATH"] = f"{self.local_lib}:{env.get('LD_LIBRARY_PATH', '')}".rstrip(":")
                res = subprocess.run([self.cmd, "--version"], capture_output=True, env=env, timeout=5)
                return res.returncode == 0
            except Exception:
                return False

    def extract_text(self, pdf_path: str) -> Optional[str]:
        if not self.available:
            # Try to re-check in case environment or paths changed
            self.cmd = self._find_tesseract_cmd("tesseract")
            self.data_path = self._find_tessdata()
            self.available = self._check_available()
            if not self.available:
                return None

        try:
            import pypdfium2 as pdfium
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = self.cmd
            config = f'--tessdata-dir "{self.data_path}"' if self.data_path else ""

            pdf = pdfium.PdfDocument(pdf_path)
            all_text = []

            for page in pdf:
                # Render page at 2.5x scale for crisp character recognition
                bitmap = page.render(scale=2.5)
                pil_image = bitmap.to_pil().convert("L")  # Grayscale

                text = pytesseract.image_to_string(pil_image, config=config)
                if text and text.strip():
                    all_text.append(text.strip())

            pdf.close()
            return "\n".join(all_text) if all_text else None

        except Exception:
            # Subprocess fallback if pytesseract wrapper hits an issue
            return self._extract_text_subprocess(pdf_path)

    def _extract_text_subprocess(self, pdf_path: str) -> Optional[str]:
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            all_text = []
            env = dict(os.environ)
            if self.local_lib.exists():
                env["LD_LIBRARY_PATH"] = f"{self.local_lib}:{env.get('LD_LIBRARY_PATH', '')}".rstrip(":")

            with tempfile.TemporaryDirectory() as tmpdir:
                for i, page in enumerate(pdf):
                    bitmap = page.render(scale=2.5)
                    img_path = os.path.join(tmpdir, f"page_{i}.png")
                    out_base = os.path.join(tmpdir, f"page_{i}")
                    bitmap.to_pil().save(img_path)

                    cmd = [self.cmd, img_path, out_base]
                    if self.data_path:
                        cmd.extend(["--tessdata-dir", self.data_path])

                    subprocess.run(cmd, capture_output=True, env=env, timeout=45)
                    txt_file = out_base + ".txt"
                    if os.path.exists(txt_file):
                        with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read().strip()
                            if content:
                                all_text.append(content)

            pdf.close()
            return "\n".join(all_text) if all_text else None
        except Exception:
            return None

    def is_scanned(self, pdf_path: str) -> bool:
        import pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]
                return len(page.chars) == 0 and len(page.images) > 0
        except Exception:
            return False
