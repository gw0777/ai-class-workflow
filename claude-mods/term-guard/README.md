# term-guard (특수체육 용어 가드)

Claude가 Write/Edit 도구로 파일을 저장하기 직전에 끼어들어, 새로 쓰는 글의 `적응체육`·`적응 체육`을 `특수체육`으로 바꿉니다. 바꾼 곳이 있으면 토스트 알림과 상태 줄에 횟수를 보여 줍니다.

- Edit의 찾을 원문(`old_string`)은 바꾸지 않습니다. 바꾸면 원문을 찾지 못해 수정이 실패합니다.
- 오류가 나면 아무것도 바꾸지 않고 원래 요청을 그대로 넘깁니다.
- Claude Code 안에서 Claude가 쓰는 글만 대상입니다. 이미 있는 파일이나 외부 API로 생성한 글은 바뀌지 않습니다.

```bash
claude plugin validate ./term-guard
claude plugin test ./term-guard
claude --plugin-dir ./term-guard
```
