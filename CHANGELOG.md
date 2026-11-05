## v0.8 — Original StarCraft sprite importer (2026-11-06)
- New `original.html` to import personally extracted original BW sprites in the browser.
- Auto-match Marine, SCV, Siege Tank and building PNG/APNG names; hide replaced low-poly meshes.
- Offline GRP + palette converter `tools/prepare_original_assets.py` and standard-library tests.
- Preserve v0.7 3D version, 35-second comic loop and no-audio rule.
- Game graphics not distributed through public GitHub or Pages; original files must be supplied locally.
- Tested PNG name import/3D toggle, synthetic GRP decoding and source JavaScript syntax. Full WebGL visual test was unavailable.

# Changelog

## v0.7 — CC0 sprite hybrid (2026-11-06)
- 공개 사용 가능한 Kenney Sci-Fi RTS CC0 스프라이트를 자동으로 불러오는 실험 모드.
- 브라우저에서 그래픽 혼합 / 기존 3D 모드 전환.
- SCV/마린/테란풍 건물 이미지 레이어 적용; 탱크 포탑 개그는 3D 형태로 계속 유지.
- 외부 이미지 오류 시 기존 3D 유지, 로컬 개인 이미지 불러오기 지원.
- 원본 Blizzard 그래픽 파일은 저장소에 포함하지 않음.
- JS 문법 검증 PASS. 브라우저 시각 검증은 환경 차단으로 미확인.

## v0.5 — Brood War silhouette pass (2026-11-05)
- 시즈탱크 경사 장갑, 궤도·바퀴, 회전 쌍포신 모델 보강
- 마린 CMC풍 어깨 장갑·헬멧·바이저·소총 및 반응 모션 유지
- SCV 쌍 작업팔·클로 모델링과 움직임 정리
- 팩토리·머신샵·아머리·디폿 지붕·경고 표식·강화패널 추가
- 숲·절벽·기지 배치와 기존 35초 무한 루프, 오디오 미포함 유지
- PC 8개 주요 시점, 모바일 1개, 재생/정지 브라우저 테스트 PASS

## v0.4 — experimental 3D (2026-11-05)
- 신규 `3d.html`: 외부 의존성이 없는 독립 WebGL2 3D 버전
- 숲·절벽·테란 시설 및 캐릭터를 실시간 3D로 재구성
- 기지 배치 및 탱크·마린·SCV 무한 루프 유지, 공장 출고문 개폐 추가
- 브라우저 7개 시점, 모바일 및 일시정지·재개 테스트 통과
- 기존 v0.3 `index.html`은 안전하게 보존



## v0.3 (2026-11-05)
- 건물 외벽 장갑·지붕·출고문 패널·리벳·경고 표시 보강
- 시즈탱크 궤도/포탑, 마린 장갑/헬멧/총, SCV 세부 외형 개선
- 숲 바닥 덤불·절벽 지층 및 프레임별 임의 색상 변경 버그 개선
- 탱크/마린/SCV의 기존 무한 루프와 구도 보존
- 8개 시점 및 모바일 화면·재생/일시정지 테스트

## v0.2 (2026-11-05)
- 탱크 포탑의 마린 응시, 마린 움찔, SCV 공사 위치 변경
- 야간 숲/절벽의 고정 아이소메트릭 장면
