"""
Diabetes Detection Agent
Detects diabetes risk from chat messages and provides risk assessment
"""

from core.state import AgentState
from diabetes_detector import detect_diabetes_from_chat

def DiabetesAgent(state: AgentState) -> AgentState:
    """Detect diabetes risk from user's message and conversation history"""
    
    question = state.get("question", "")
    conversation_history = state.get("conversation_history", [])
    
    # Check if the message is related to diabetes symptoms
    diabetes_keywords = [
        'diabetes', 'diabetic', 'blood sugar', 'glucose', 'insulin',
        'sugar level', 'high glucose', 'diabetes symptoms', 'diabetes risk',
        'pregestational', 'gestational diabetes', 'type 1', 'type 2',
        'thirsty', 'frequent urination', 'weight loss', 'blurred vision'
    ]
    
    question_lower = question.lower()
    is_diabetes_related = any(keyword in question_lower for keyword in diabetes_keywords)
    
    # Also check if user mentions medical values that could indicate diabetes screening
    has_medical_values = any(keyword in question_lower for keyword in [
        'glucose', 'blood sugar', 'bmi', 'blood pressure', 'bp',
        'age', 'pregnancy', 'pregnancies', 'insulin'
    ])
    
    if is_diabetes_related or has_medical_values:
        try:
            # Run diabetes detection
            result = detect_diabetes_from_chat(question, conversation_history)
            
            if result['success']:
                # Add diabetes detection result to state
                state["diabetes_detection"] = {
                    "has_risk": result['has_risk'],
                    "probability": result['probability'],
                    "features": result['features'],
                    "message": result['message']
                }
                state["diabetes_detected"] = True
                
                # Add diabetes information to the generation if not already present
                if not state.get("generation"):
                    state["generation"] = result['message']
                    state["source"] = "Diabetes Risk Assessment"
                else:
                    # Append diabetes info to existing generation
                    state["generation"] += f"\n\n🔍 {result['message']}"
            else:
                state["diabetes_detected"] = False
                
        except Exception as e:
            print(f"Error in DiabetesAgent: {str(e)}")
            state["diabetes_detected"] = False
    else:
        state["diabetes_detected"] = False
    
    return state

