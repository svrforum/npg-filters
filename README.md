# NPG Filter Lists

Nginx Proxy Guard(NPG)를 위한 커뮤니티 기반 보안 필터 리스트 저장소입니다.

NPG에서 이 저장소의 필터 리스트를 구독하면, 알려진 악성 IP, 봇넷 대역, 공격 도구 User-Agent 등을 자동으로 차단할 수 있습니다.

## 필터 타입

| 타입 | 디렉토리 | 설명 |
|------|----------|------|
| IP | `lists/ips/` | 개별 IP 주소 차단 |
| CIDR | `lists/cidrs/` | IP 대역(CIDR) 차단 |
| User Agent | `lists/user-agents/` | User-Agent 패턴(정규식) 차단 |

## JSON 포맷

각 필터 리스트 파일은 다음 형식을 따릅니다:

```json
{
  "name": "리스트 이름",
  "description": "리스트 설명",
  "type": "ip | cidr | user_agent",
  "expires": "6h | 12h | 24h | 48h",
  "entries": [
    {
      "value": "차단할 값 (IP, CIDR, 또는 정규식)",
      "reason": "차단 사유",
      "added": "2026-03-31",
      "contributor": "기여자 GitHub ID"
    }
  ]
}
```

- `expires`: NPG가 리스트를 다시 가져오는 주기
- `entries`: 최대 5,000개까지 허용

## 기여 방법

1. 이 저장소를 **Fork** 합니다.
2. 적절한 디렉토리(`lists/ips/`, `lists/cidrs/`, `lists/user-agents/`)에 JSON 파일을 추가하거나 수정합니다.
3. **Pull Request**를 생성합니다.
4. CI가 자동으로 유효성 검사를 수행합니다.
5. 리뷰 후 병합됩니다.

## 규칙

- 모든 항목에 `reason` (차단 사유)을 반드시 포함해야 합니다.
- **사설/예약 IP 금지**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1/128`, `fc00::/7`, `fe80::/10` 대역은 등록할 수 없습니다.
- 파일당 최대 **5,000개** 항목까지 허용됩니다.
- 같은 타입 내에서 **중복 값은 금지**됩니다 (파일 내 및 파일 간).
- User Agent 타입의 `value`는 유효한 **정규식**이어야 합니다.
- 파일은 타입에 맞는 디렉토리에 위치해야 합니다.

## NPG 연동 방법

1. NPG 관리 패널에서 **Settings > Filter Subscriptions** 메뉴로 이동합니다.
2. 구독할 필터 리스트의 Raw URL을 추가합니다.
   - 예: `https://raw.githubusercontent.com/svrforum/npg-filters/main/lists/user-agents/malicious-tools.json`
3. NPG가 `expires`에 설정된 주기마다 자동으로 리스트를 갱신합니다.

## 외부 Plaintext 리스트 지원

NPG는 이 저장소의 JSON 형식 외에도, 줄 단위 plaintext 형식의 외부 필터 리스트도 지원합니다. IP/CIDR 리스트를 제공하는 외부 URL을 직접 구독 URL로 등록할 수 있습니다.

## 인덱스

`index.json` 파일은 CI에 의해 자동 생성되며, 이 저장소에 포함된 모든 필터 리스트의 메타데이터를 담고 있습니다. NPG는 이 인덱스를 사용하여 사용 가능한 필터 리스트 목록을 표시합니다.
