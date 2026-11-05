# 로컬 스타1 원본 스프라이트 프레임 설정

실제 원본 스프라이트 파일과 매니페스트는 **개인 PC의 `local_assets/`** 에만 둔다. 공개 저장소에는 파일을 올리지 않는다.

## 원리

- 원본 브루드워 유닛 GRP는 단순한 GIF가 아니다. 방향이 있는 유닛은 17방향씩 프레임을 묶는다.
- `iscript.bin`이 어떤 프레임을 언제 보여줄지 결정하며, 탱크 포탑 등은 별도 이미지를 겹쳐 그린다.
- 변환 도구는 이미지 전체 프레임을 PNG로 추출하고, 기본적으로 한 방향을 고정해 둔다. 부드러운 움직임을 원하면 다음 예시처럼 해당 유닛에 맞는 프레임 인덱스를 지정해야 한다.

## 예시

아래 파일명은 **가상의 로컬 테스트 PNG 4개**를 사용하는 예시다. 실제 게임에서 추출한 프레임 배열과 다를 수 있다.

```json
{
  "format": "original-starcraft-local-pack-v2",
  "sprites": {
    "marine": {
      "frames": ["frames/marine/marine_0000.png", "frames/marine/marine_0001.png", "frames/marine/marine_0002.png", "frames/marine/marine_0003.png"],
      "fps": 4,
      "width": 74,
      "height": 100,
      "anchorX": 0.5,
      "anchorY": 0.88,
      "states": {
        "idle": [0, 1, 0, 2],
        "watch": [2],
        "react": [3, 3, 2, 0]
      }
    },
    "scv": {
      "src": "scv.png",
      "width": 120,
      "height": 92
    }
  }
}
```

- `states.idle`은 경계 대기, `react`는 탱크에 놀라는 순간, `watch`는 응시 상태, `work`는 SCV 공사, `move`는 전차 이동에 적용된다.
- `fps`는 지정된 상태 프레임의 초당 변화 횟수다. 단순 PNG 시퀀스도 지원하며 APNG는 브라우저 자체 재생이므로 정확한 일시정지 동기화를 보장하지 않는다.
- 누락된 상태는 `idle`로 대체된다. 행동 매핑이 전혀 없다면 안정적인 첫 방향 프레임을 보여준다.
- 탱크의 포탑을 제대로 분리해 표현하려면 `siege_tank_look`으로 별도 포탑 이미지를 제공해야 한다. 이를 제공하지 않으면 탱크 이미지가 표시되더라도 원본 포탑 방향 재현에는 한계가 있다.

## 한계와 이후 과제

1. iscript/방향 매핑을 자동 해석하는 기능은 아직 없다.
2. 원본 스타1 그래픽의 레이어별 오클루전(건물 뒤 가림)은 3D 메시만큼 정확하지 않다.
3. 원본 그래픽 데이터 자체는 포함하거나 공개 링크로 다운로드하지 않는다.

## 참고 자료

- broodwar-live. (n.d.). *BW asset extraction pipeline* [Computer software]. GitHub. https://github.com/broodwar-live/assets-pipeline
- scmJS. (n.d.). *How units are drawn*. https://docs.scmjs.dev/game-data/how-units-are-drawn/