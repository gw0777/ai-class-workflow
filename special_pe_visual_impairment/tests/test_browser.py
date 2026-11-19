"""브라우저 검사(browser_check.cjs)를 unittest로 실행합니다.

Node.js용 Playwright가 없는 환경(예: 기본 CI)에서는 건너뜁니다.
"""
import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("browser_check.cjs")


def _playwright_available():
    node = shutil.which("node")
    if not node:
        return False
    probe = subprocess.run([node, "-e", "require('playwright')"], capture_output=True)
    return probe.returncode == 0


@unittest.skipUnless(_playwright_available(), "Node.js용 Playwright가 없어 브라우저 검사를 건너뜁니다")
class BrowserCheckTest(unittest.TestCase):
    def test_browser_checks_pass(self):
        run = subprocess.run(["node", str(SCRIPT)], capture_output=True, text=True, timeout=300)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
