"""
특수체육(APA) 프로그램 제안 전문가 앱
Adapted Physical Activity Program Expert App

비전공자도 쉽게 사용할 수 있는 특수체육 프로그램 구성 지원 시스템
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List
import os

# 페이지 설정
st.set_page_config(
    page_title="APA 프로그램 전문가",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'program_data' not in st.session_state:
    st.session_state.program_data = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# APA 지식 베이스
APA_KNOWLEDGE_BASE = {
    "기본_개념": {
        "특수체육이란": """
        특수체육(Adapted Physical Activity)은 장애가 있거나 특별한 요구를 가진 학생들을 위한
        맞춤형 체육 프로그램입니다. 개인의 능력과 필요에 따라 조정된 활동을 제공합니다.
        """,
        "핵심_원칙": [
            "개별화: 각 학생의 능력과 필요에 맞춤",
            "포용성: 모든 학생이 참여할 수 있도록",
            "적응성: 활동과 규칙을 유연하게 조정",
            "안전성: 안전한 환경에서 활동 진행",
            "발달적 접근: 단계적 기술 발달 지원"
        ]
    },
    "프로그램_구성요소": {
        "평가": [
            "학생의 현재 신체 능력 평가",
            "운동 기술 수준 파악",
            "개별 교육 목표 설정",
            "건강 및 안전 고려사항 확인"
        ],
        "계획": [
            "단기 및 장기 목표 수립",
            "적절한 활동 선택",
            "필요한 장비 및 시설 준비",
            "수정 및 적응 전략 계획"
        ],
        "실행": [
            "체계적인 교수 방법 적용",
            "긍정적 강화 제공",
            "진행 상황 모니터링",
            "필요시 즉각적인 조정"
        ],
        "평가_및_수정": [
            "정기적인 진도 평가",
            "목표 달성도 확인",
            "프로그램 효과성 검토",
            "필요한 수정사항 적용"
        ]
    },
    "교수_전략": {
        "직접교수법": "명확한 시범과 단계별 지도를 통한 기술 습득",
        "협동학습": "팀 활동을 통한 사회성 및 운동 기술 발달",
        "게임중심접근": "게임을 통해 즐겁게 기술 학습",
        "과제분석": "복잡한 기술을 작은 단계로 나누어 지도",
        "또래교수": "또래 학생이 도움을 주는 협력적 학습"
    },
    "적용_활동": {
        "개인_활동": ["육상", "수영", "체조", "요가", "필라테스"],
        "팀_활동": ["농구", "배구", "축구", "야구", "플로어볼"],
        "리듬_활동": ["댄스", "리듬체조", "에어로빅"],
        "뉴스포츠": ["플라잉디스크", "킨볼", "티볼"],
        "전통활동": ["태권도", "검도", "씨름", "전통놀이"]
    }
}

# 프로그램 템플릿
PROGRAM_TEMPLATES = {
    "초급": {
        "기간": "8주",
        "빈도": "주 2회",
        "시간": "40분",
        "목표": "기본 운동 능력 향상 및 체육 활동 친숙화"
    },
    "중급": {
        "기간": "12주",
        "빈도": "주 3회",
        "시간": "50분",
        "목표": "특정 운동 기술 습득 및 체력 증진"
    },
    "고급": {
        "기간": "16주",
        "빈도": "주 3-4회",
        "시간": "60분",
        "목표": "고급 기술 습득 및 경기 참여 능력 향상"
    }
}

def get_apa_answer(question: str) -> str:
    """질문에 대한 APA 관련 답변 제공"""
    question_lower = question.lower()

    # 키워드 기반 응답
    if "특수체육" in question or "apa" in question_lower:
        return APA_KNOWLEDGE_BASE["기본_개념"]["특수체육이란"]
    elif "원칙" in question or "기본" in question:
        principles = "\n".join([f"• {p}" for p in APA_KNOWLEDGE_BASE["기본_개념"]["핵심_원칙"]])
        return f"특수체육의 핵심 원칙:\n\n{principles}"
    elif "교수" in question or "지도" in question or "방법" in question:
        strategies = "\n\n".join([f"**{k}**: {v}" for k, v in APA_KNOWLEDGE_BASE["교수_전략"].items()])
        return f"주요 교수 전략:\n\n{strategies}"
    elif "활동" in question or "종목" in question:
        activities = ""
        for category, items in APA_KNOWLEDGE_BASE["적용_활동"].items():
            activities += f"\n\n**{category}**: {', '.join(items)}"
        return f"추천 활동 종목:{activities}"
    elif "평가" in question:
        assessment = "\n".join([f"• {item}" for item in APA_KNOWLEDGE_BASE["프로그램_구성요소"]["평가"]])
        return f"학생 평가 요소:\n\n{assessment}"
    else:
        return """
        특수체육 프로그램에 대해 더 구체적인 질문을 해주세요. 예:
        • 특수체육의 기본 원칙은 무엇인가요?
        • 어떤 교수 방법을 사용할 수 있나요?
        • 추천하는 활동 종목은 무엇인가요?
        • 학생을 어떻게 평가하나요?
        """

def generate_program_proposal(data: Dict) -> str:
    """프로그램 제안서 생성"""
    template = PROGRAM_TEMPLATES.get(data.get('level', '초급'))

    # 날짜 포맷팅을 별도로 처리
    current_date = datetime.now().strftime('%Y년 %m월 %d일')

    # 기본값들을 미리 정의 (f-string 내 백슬래시 문제 해결)
    default_objectives = '• 기본 운동 능력 향상\n• 신체 활동 참여 증진\n• 사회성 발달'
    default_activities = '• 준비운동 및 스트레칭\n• 기본 운동 기술 연습\n• 게임 및 팀 활동\n• 정리운동'
    default_equipment = '• 기본 체육 장비 (공, 콘, 매트 등)\n• 안전 장비\n• 보조 교구'

    proposal = f"""
# 특수체육 프로그램 제안서

## 1. 프로그램 개요
- **프로그램명**: {data.get('program_name', 'APA 프로그램')}
- **대상**: {data.get('target_group', '특수교육 대상 학생')}
- **인원**: {data.get('num_students', '10-15')}명
- **수준**: {data.get('level', '초급')}

## 2. 프로그램 목표
{data.get('objectives', default_objectives)}

## 3. 운영 계획
- **기간**: {template['기간']}
- **빈도**: {template['빈도']}
- **회당 시간**: {template['시간']}
- **장소**: {data.get('location', '체육관 또는 운동장')}

## 4. 주요 활동
{data.get('activities', default_activities)}

## 5. 교수 전략
- **주요 방법**: {data.get('teaching_method', '직접교수법, 또래교수')}
- **적용 방안**:
  • 명확한 시범과 설명 제공
  • 단계별 난이도 조정
  • 긍정적 피드백 제공
  • 개별 지도 및 지원

## 6. 필요 장비 및 자원
{data.get('equipment', default_equipment)}

## 7. 안전 및 유의사항
- 사전 건강 상태 확인
- 안전한 환경 조성
- 응급 상황 대비 계획
- 개별 학생의 특성 고려

## 8. 평가 계획
- **평가 방법**: 관찰 평가, 기술 체크리스트, 자기평가
- **평가 시기**: 프로그램 시작 전, 중간, 종료 후
- **평가 내용**:
  • 운동 기술 발달
  • 참여도 및 태도
  • 사회성 발달
  • 체력 변화

## 9. 기대 효과
- 신체적 건강 및 체력 향상
- 운동 기술 습득
- 자신감 및 자존감 향상
- 사회성 및 협력 능력 발달

---
*생성일: {current_date}*
*본 제안서는 APA 프로그램 전문가 앱을 통해 생성되었습니다.*
"""
    return proposal

def main():
    # 사이드바
    st.sidebar.title("🏃 APA 프로그램 전문가")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio(
        "메뉴 선택",
        ["🏠 홈", "❓ Q&A", "📝 프로그램 생성", "📚 지식 베이스", "💡 가이드"]
    )

    # 메인 컨텐츠
    if menu == "🏠 홈":
        st.title("특수체육 프로그램 제안 전문가 앱")
        st.markdown("### 비전공자를 위한 맞춤형 APA 프로그램 지원 시스템")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("**🎯 목적**\n\n특수체육 비전공자도 쉽게 체육 프로그램을 구성할 수 있도록 전문적인 가이드와 도구를 제공합니다.")

        with col2:
            st.success("**✨ 주요 기능**\n\n• AI 기반 Q&A\n• 프로그램 자동 생성\n• 교수 전략 안내\n• 활동 추천")

        with col3:
            st.warning("**📖 활용 방법**\n\n1. Q&A에서 질문\n2. 프로그램 생성 도구 사용\n3. 지식 베이스 참고")

        st.markdown("---")
        st.subheader("빠른 시작")
        st.markdown("""
        1. **Q&A 섹션**: 특수체육에 대한 질문을 하고 즉시 답변을 받으세요
        2. **프로그램 생성**: 단계별 양식을 작성하여 맞춤형 프로그램 제안서를 생성하세요
        3. **지식 베이스**: 특수체육 관련 핵심 정보와 전략을 탐색하세요
        4. **가이드**: 상황별 가이드라인과 팁을 확인하세요
        """)

    elif menu == "❓ Q&A":
        st.title("특수체육 Q&A")
        st.markdown("특수체육과 프로그램 구성에 대해 무엇이든 질문하세요!")

        # 채팅 히스토리 표시
        for chat in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(chat["question"])
            with st.chat_message("assistant"):
                st.write(chat["answer"])

        # 질문 입력
        question = st.chat_input("질문을 입력하세요...")

        if question:
            # 사용자 질문 표시
            with st.chat_message("user"):
                st.write(question)

            # 답변 생성 및 표시
            answer = get_apa_answer(question)
            with st.chat_message("assistant"):
                st.write(answer)

            # 히스토리에 추가
            st.session_state.chat_history.append({
                "question": question,
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            })

        # 자주 묻는 질문
        st.markdown("---")
        st.subheader("💡 자주 묻는 질문")

        faq_col1, faq_col2 = st.columns(2)

        with faq_col1:
            if st.button("특수체육의 기본 원칙은?"):
                st.info(get_apa_answer("특수체육의 기본 원칙"))

            if st.button("어떤 교수 방법을 사용하나요?"):
                st.info(get_apa_answer("교수 방법"))

        with faq_col2:
            if st.button("추천 활동 종목은?"):
                st.info(get_apa_answer("활동 종목"))

            if st.button("학생 평가는 어떻게 하나요?"):
                st.info(get_apa_answer("평가"))

    elif menu == "📝 프로그램 생성":
        st.title("프로그램 제안서 생성")
        st.markdown("아래 양식을 작성하여 맞춤형 특수체육 프로그램 제안서를 생성하세요.")

        with st.form("program_form"):
            st.subheader("1️⃣ 기본 정보")
            col1, col2 = st.columns(2)

            with col1:
                program_name = st.text_input("프로그램명", "즐거운 특수체육")
                target_group = st.text_input("대상 그룹", "초등학교 특수학급 학생")
                num_students = st.text_input("예상 인원", "10-15명")

            with col2:
                level = st.selectbox("수준", ["초급", "중급", "고급"])
                location = st.text_input("장소", "체육관")
                teaching_method = st.multiselect(
                    "교수 방법",
                    list(APA_KNOWLEDGE_BASE["교수_전략"].keys()),
                    default=["직접교수법"]
                )

            st.subheader("2️⃣ 프로그램 목표")
            objectives = st.text_area(
                "목표 (각 줄에 하나씩)",
                "• 기본 운동 능력 향상\n• 신체 활동 참여 증진\n• 사회성 발달",
                height=100
            )

            st.subheader("3️⃣ 주요 활동")
            activities = st.text_area(
                "활동 내용 (각 줄에 하나씩)",
                "• 준비운동 및 스트레칭 (10분)\n• 기본 운동 기술 연습 (20분)\n• 게임 및 팀 활동 (15분)\n• 정리운동 (5분)",
                height=150
            )

            st.subheader("4️⃣ 필요 장비")
            equipment = st.text_area(
                "장비 및 자원",
                "• 소프트볼 (10개)\n• 안전 콘 (20개)\n• 체조 매트 (5개)\n• 보조 교구",
                height=100
            )

            submitted = st.form_submit_button("📄 제안서 생성", use_container_width=True)

            if submitted:
                program_data = {
                    'program_name': program_name,
                    'target_group': target_group,
                    'num_students': num_students,
                    'level': level,
                    'location': location,
                    'teaching_method': ', '.join(teaching_method),
                    'objectives': objectives,
                    'activities': activities,
                    'equipment': equipment
                }

                st.session_state.program_data = program_data
                proposal = generate_program_proposal(program_data)

                st.success("✅ 프로그램 제안서가 생성되었습니다!")
                st.markdown("---")
                st.markdown(proposal)

                # 다운로드 버튼
                st.download_button(
                    label="📥 제안서 다운로드 (Markdown)",
                    data=proposal,
                    file_name=f"APA_프로그램_제안서_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )

    elif menu == "📚 지식 베이스":
        st.title("특수체육 지식 베이스")
        st.markdown("특수체육 프로그램 구성에 필요한 핵심 정보를 탐색하세요.")

        tab1, tab2, tab3, tab4 = st.tabs(["📖 기본 개념", "🔧 프로그램 구성", "👨‍🏫 교수 전략", "⚽ 활동 종목"])

        with tab1:
            st.subheader("특수체육(APA)이란?")
            st.info(APA_KNOWLEDGE_BASE["기본_개념"]["특수체육이란"])

            st.subheader("핵심 원칙")
            for principle in APA_KNOWLEDGE_BASE["기본_개념"]["핵심_원칙"]:
                st.markdown(f"✅ {principle}")

        with tab2:
            st.subheader("프로그램 구성 4단계")

            for phase, items in APA_KNOWLEDGE_BASE["프로그램_구성요소"].items():
                with st.expander(f"**{phase}**", expanded=True):
                    for item in items:
                        st.markdown(f"• {item}")

        with tab3:
            st.subheader("주요 교수 전략")

            for strategy, description in APA_KNOWLEDGE_BASE["교수_전략"].items():
                st.markdown(f"**{strategy}**")
                st.write(description)
                st.markdown("---")

        with tab4:
            st.subheader("추천 활동 종목")

            for category, activities in APA_KNOWLEDGE_BASE["적용_활동"].items():
                st.markdown(f"**{category}**")
                cols = st.columns(5)
                for idx, activity in enumerate(activities):
                    cols[idx % 5].button(activity, key=f"{category}_{activity}")
                st.markdown("")

    elif menu == "💡 가이드":
        st.title("프로그램 구성 가이드")

        guide_type = st.selectbox(
            "가이드 선택",
            ["첫 프로그램 시작하기", "장애 유형별 고려사항", "안전 관리", "효과적인 피드백"]
        )

        if guide_type == "첫 프로그램 시작하기":
            st.markdown("""
            ## 🎯 특수체육 프로그램 시작 가이드

            ### 1단계: 학생 이해하기
            - 학생들의 장애 유형과 정도 파악
            - 현재 신체 능력 수준 평가
            - 흥미와 선호도 조사
            - 건강 상태 및 주의사항 확인

            ### 2단계: 목표 설정하기
            - **SMART 목표** 설정 (구체적, 측정가능, 달성가능, 관련성, 시간제한)
            - 예: "8주 동안 공 던지기 거리를 5m 향상시킨다"

            ### 3단계: 활동 선택하기
            - 학생의 능력에 적합한 활동 선택
            - 다양한 활동으로 흥미 유지
            - 안전하고 즐거운 활동 우선

            ### 4단계: 환경 준비하기
            - 안전한 공간 확보
            - 필요한 장비 준비
            - 보조 인력 배치

            ### 5단계: 실행 및 조정하기
            - 계획대로 실행
            - 학생 반응 관찰
            - 필요시 즉시 수정
            - 긍정적 피드백 제공
            """)

        elif guide_type == "장애 유형별 고려사항":
            st.markdown("""
            ## 🎯 장애 유형별 프로그램 조정 가이드

            ### 지적장애
            - 간단하고 명확한 지시
            - 반복적인 연습 기회 제공
            - 시각적 자료 활용
            - 즉각적인 피드백

            ### 자폐스펙트럼장애
            - 구조화된 일과와 규칙
            - 예측 가능한 환경
            - 감각 자극 조절
            - 개별 공간 제공

            ### 지체장애
            - 접근 가능한 시설
            - 보조 기구 활용
            - 이동 동선 고려
            - 휠체어 활동 적용

            ### 시각장애
            - 청각 신호 활용
            - 촉각 단서 제공
            - 공간 방향 안내
            - 밝은 색상 장비 사용

            ### 청각장애
            - 시각적 시범 강화
            - 수화 또는 문자 활용
            - 진동 신호 사용
            - 얼굴 보고 대화
            """)

        elif guide_type == "안전 관리":
            st.markdown("""
            ## 🛡️ 안전 관리 가이드

            ### 사전 준비
            ✅ 건강 상태 체크리스트 작성
            ✅ 응급 연락망 구축
            ✅ 응급처치 키트 준비
            ✅ 안전 장비 점검

            ### 환경 안전
            ✅ 바닥 상태 확인 (미끄럼 방지)
            ✅ 장애물 제거
            ✅ 적절한 조명
            ✅ 비상구 확보

            ### 활동 중 안전
            ✅ 적절한 준비운동
            ✅ 학생 대 지도자 비율 준수
            ✅ 지속적인 관찰
            ✅ 수분 섭취 시간 제공

            ### 응급 상황 대응
            ✅ 응급 상황 프로토콜 수립
            ✅ 정기적인 안전 교육
            ✅ 사고 보고 체계 마련
            """)

        elif guide_type == "효과적인 피드백":
            st.markdown("""
            ## 💬 효과적인 피드백 제공 가이드

            ### 긍정적 피드백
            - **즉시성**: 좋은 행동 직후 칭찬
            - **구체성**: "잘했어" 대신 "공을 정확히 던졌어"
            - **진정성**: 진심 어린 칭찬
            - **일관성**: 지속적인 긍정적 강화

            ### 교정적 피드백
            - **긍정으로 시작**: "노력은 좋았어, 이제 이렇게 해보자"
            - **시범 제공**: 올바른 방법 직접 보여주기
            - **단계적 접근**: 한 번에 하나씩 수정
            - **격려로 마무리**: "다음에는 더 잘할 거야"

            ### 피드백 예시
            ✅ "와! 공을 두 손으로 잡았네! 훌륭해!"
            ✅ "발을 어깨 너비로 벌리니까 균형이 더 좋아졌어!"
            ✅ "이번엔 거의 다 했어! 한 번 더 해보자!"
            ✅ "너의 노력이 대단해! 계속 연습하면 잘하게 될 거야!"
            """)

    # 푸터
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📞 도움이 필요하신가요?
    - 각 섹션의 가이드를 참고하세요
    - Q&A에서 질문하세요
    - 지식 베이스를 탐색하세요
    """)

    st.sidebar.info("**버전**: 1.0.0\n\n**개발**: APA 프로그램 전문가 시스템")

if __name__ == "__main__":
    main()
