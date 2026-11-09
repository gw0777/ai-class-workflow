// 특수체육 시각장애 교재 브라우저 검사 (Node.js + Playwright)
// 실행: node special_pe_visual_impairment/tests/browser_check.cjs [--shots <폴더>]
// 외부 글꼴 요청은 빈 응답으로 대신하므로 네트워크 없이도 같은 결과가 나옵니다.
const path = require('path');
const { chromium } = require('playwright');

const FILE = 'file://' + path.resolve(__dirname, '..', 'index.html');
const shotsAt = process.argv.indexOf('--shots');
const SHOTS = shotsAt > -1 ? process.argv[shotsAt + 1] : null;
let failures = 0;

function check(name, ok, detail) {
  if (ok) console.log('ok   ' + name);
  else { failures++; console.log('FAIL ' + name + (detail ? '  :: ' + detail : '')); }
}

async function open(browser, opts) {
  const ctx = await browser.newContext(opts);
  await ctx.route(/^https?:\/\//, route => route.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(FILE);
  return { ctx, page, errors };
}

const txt = async (page, sel) => ((await page.textContent(sel)) || '').trim();
const noHScroll = page => page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);

(async () => {
  const browser = await chromium.launch();
  try {
    // 1) 데스크톱 1280px, 밝은 테마
    {
      const { ctx, page, errors } = await open(browser, { viewport: { width: 1280, height: 900 } });
      check('desktop: 스크립트·콘솔 오류 없음', errors.length === 0, errors.join(' | '));
      const [sw, iw] = await noHScroll(page);
      check('desktop: 가로 스크롤 없음', sw <= iw, `${sw} > ${iw}`);
      check('제목', (await page.title()) === '특수체육 시각장애 교재');
      check('표지 카드 수 51', (await txt(page, '#fcTotalCover')) === '51');
      check('덱 시작 1 / 51', (await txt(page, '#dkPos')) === '1 / 51');
      const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      check('밝은 테마 배경', bg === 'rgb(255, 255, 255)', bg);

      // 카드 뒤집기와 표시
      await page.click('#dkCard');
      check('덱: 누르면 뒤집힘', (await page.getAttribute('#dkCard', 'aria-pressed')) === 'true');
      check('덱: 뒷면이 낭독기에 열림', (await page.getAttribute('#dkBack', 'aria-hidden')) === 'false');
      check('덱: 앞면은 낭독기에서 숨김', (await page.getAttribute('#dkFront', 'aria-hidden')) === 'true');
      check('덱: 뒷면에도 질문 표시', (await txt(page, '#dkBackQ')) === '질문: ' + (await txt(page, '#dkQ')));
      const firstId = await page.evaluate(() => document.querySelector('details.fc').dataset.fc);
      await page.click('#dkKnow');
      check('덱: 알아요 뒤 다음 카드(2 / 51)', (await txt(page, '#dkPos')) === '2 / 51');
      check('덱: 알아요 1 집계', (await txt(page, '#dkStats')).startsWith('알아요 1 · 다시 0'));
      check('장 안 카드에 알아요 표시', (await page.getAttribute(`details.fc[data-fc="${firstId}"]`, 'data-state')) === 'k');
      check('덱: 다음 카드는 앞면부터', (await page.getAttribute('#dkCard', 'aria-pressed')) === 'false');

      // 키보드
      await page.focus('#dkCard');
      await page.keyboard.press('ArrowRight');
      check('키보드: → 로 다음 카드(3 / 51)', (await txt(page, '#dkPos')) === '3 / 51');
      await page.keyboard.press('Space');
      check('키보드: Space 로 뒤집기', (await page.getAttribute('#dkCard', 'aria-pressed')) === 'true');
      await page.keyboard.press('ArrowLeft');
      check('키보드: ← 로 이전 카드(2 / 51)', (await txt(page, '#dkPos')) === '2 / 51');

      // 장별 묶음과 「다시 볼 카드만」
      await page.click('a.go[data-deck="p1-c1"]');
      check('장 링크: 1부 1장 카드 5장', (await txt(page, '#dkPos')) === '1 / 5');
      check('장 링크: 선택 상자도 바뀜', (await page.inputValue('#dkFilter')) === 'p1-c1');
      await page.check('#dkOnlyReview');
      check('다시 볼 카드가 없으면 빈 상태 안내', await page.isVisible('#dkEmpty'));
      check('빈 상태에서 버튼 잠김', await page.isDisabled('#dkKnow'));
      await page.uncheck('#dkOnlyReview');
      await page.click('#dkNext');
      await page.click('#dkAgain');
      await page.check('#dkOnlyReview');
      check('다시 볼 카드만: 1 / 1', (await txt(page, '#dkPos')) === '1 / 1');
      await page.click('#dkKnow');
      check('다시 볼 카드를 모두 마치면 빈 상태', await page.isVisible('#dkEmpty'));
      await page.uncheck('#dkOnlyReview');
      await page.selectOption('#dkFilter', 'part:p2');
      check('묶음: 2부 전체 23장', (await txt(page, '#dkPos')) === '1 / 23');
      await page.selectOption('#dkFilter', 'all');

      // 진도와 과제 카드
      await page.check('#p1-c1-done');
      check('진도 문구', (await txt(page, '#progTxt')) === '끝낸 장 1 / 16');
      check('차례 1부 집계', (await txt(page, '#c-p1')) === '1/7');
      check('차례 끝낸 장 표시', await page.evaluate(() => document.querySelector('[data-toc="p1-c1"]').classList.contains('is-done')));
      for (let i = 1; i <= 4; i++) await page.check(`#p1-c1-tc1-${i}`);
      check('과제 카드: 통과 표시', await page.evaluate(() => document.getElementById('p1-c1-tc1').hasAttribute('data-pass')));
      check('과제 카드: 기준 4/4', (await txt(page, '#p1-c1-tc1 .tc-count')) === '기준 4/4');
      check('과제 카드: 통과 배지 보임', await page.isVisible('#p1-c1-tc1 .tc-pass'));

      // 다시 열어도 남아 있는지
      await page.reload();
      check('저장: 끝낸 장 유지', await page.isChecked('#p1-c1-done'));
      check('저장: 알아요 카드 유지', (await page.getAttribute(`details.fc[data-fc="${firstId}"]`, 'data-state')) === 'k');
      check('저장: 과제 카드 통과 유지', await page.evaluate(() => document.getElementById('p1-c1-tc1').hasAttribute('data-pass')));

      // 복사 버튼(클립보드 권한이 없으면 글을 선택해 주는 대체 동작). 처리가 비동기이므로 응답을 기다린 뒤 판정한다.
      const copy = page.locator('figure.prompt .copy').first();
      await copy.click();
      await page.waitForFunction(b => b.textContent.trim() !== '복사', await copy.elementHandle(), { timeout: 3000 }).catch(() => {});
      const ct = ((await copy.textContent()) || '').trim();
      check('복사 버튼 응답', ct === '복사됨' || ct === '선택됨: 복사하세요', ct);

      // 보기 설정
      await page.click('[data-fs-set="l"]');
      check('글자 크게: 18px', await page.evaluate(() => getComputedStyle(document.documentElement).fontSize === '18px'));
      await page.click('[data-fs-set="m"]');
      check('글자 보통: 16px', await page.evaluate(() => getComputedStyle(document.documentElement).fontSize === '16px'));
      await page.click('#hcBtn');
      check('고대비 켜짐', (await page.getAttribute('html', 'data-contrast')) === 'high');
      const line = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--line').trim());
      check('고대비: 선 색이 글자색과 같음', line === '#151515', line);
      await page.click('#hcBtn');

      // 기록 지우기(두 번 눌러야 지워짐)
      await page.click('#dkReset');
      check('기록 지우기: 한 번 더 확인', (await txt(page, '#dkReset')).includes('한 번 더'));
      await page.click('#dkReset');
      check('기록 지우기: 카드 기록 초기화', (await txt(page, '#dkStats')).startsWith('알아요 0 · 다시 0'));
      check('desktop: 끝까지 오류 없음', errors.length === 0, errors.join(' | '));
      if (SHOTS) {
        await page.goto(FILE);
        await page.screenshot({ path: path.join(SHOTS, 'desktop-top.png') });
        await page.locator('#p1-c1-tc1').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(SHOTS, 'desktop-task-card.png') });
        await page.locator('#deck').scrollIntoViewIfNeeded();
        await page.click('#dkCard');
        await page.waitForTimeout(600);
        await page.screenshot({ path: path.join(SHOTS, 'desktop-deck.png') });
      }
      await ctx.close();
    }

    // 1-2) 클립보드 권한이 있으면 프롬프트 글이 그대로 복사되는지
    {
      const { ctx, page, errors } = await open(browser, { viewport: { width: 1280, height: 900 }, permissions: ['clipboard-read', 'clipboard-write'] });
      const copy = page.locator('figure.prompt .copy').first();
      await copy.click();
      await page.waitForFunction(b => b.textContent.trim() !== '복사', await copy.elementHandle(), { timeout: 3000 }).catch(() => {});
      check('복사: 권한이 있으면 「복사됨」', ((await copy.textContent()) || '').trim() === '복사됨');
      const [clip, pre] = await page.evaluate(async () => [await navigator.clipboard.readText(), document.querySelector('figure.prompt pre').innerText]);
      check('복사: 클립보드 내용이 프롬프트와 같음', clip === pre && clip.startsWith('[역할]'), clip.slice(0, 40));
      check('복사: 오류 없음', errors.length === 0, errors.join(' | '));
      await ctx.close();
    }

    // 2) 휴대폰 390px, 다크 테마
    {
      const { ctx, page, errors } = await open(browser, { viewport: { width: 390, height: 844 }, colorScheme: 'dark' });
      let [sw, iw] = await noHScroll(page);
      check('mobile: 가로 스크롤 없음', sw <= iw, `${sw} > ${iw}`);
      const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      check('다크 테마 배경', bg === 'rgb(18, 18, 18)', bg);
      check('mobile: 차례 접힘', await page.evaluate(() => [...document.querySelectorAll('nav.toc details')].every(d => !d.open)));
      await page.click('[data-fs-set="xl"]');
      [sw, iw] = await noHScroll(page);
      check('mobile 아주 큰 글자: 가로 스크롤 없음', sw <= iw, `${sw} > ${iw}`);
      await page.click('#hcBtn');
      const line = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--line').trim());
      check('다크 고대비: 선 색이 밝은 글자색', line === '#f3f1ea', line);
      check('mobile: 오류 없음', errors.length === 0, errors.join(' | '));
      if (SHOTS) {
        await page.click('#hcBtn');
        await page.click('[data-fs-set="m"]');
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({ path: path.join(SHOTS, 'mobile-dark-top.png') });
        await page.locator('#p1-c2 .safe.stop').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(SHOTS, 'mobile-dark-safety.png') });
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
  console.log(failures ? `\n${failures}개 검사 실패` : '\n브라우저 검사 모두 통과');
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
