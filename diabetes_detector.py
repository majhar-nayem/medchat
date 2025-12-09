"""
Diabetes Detection Service
Extracts symptoms and medical values from chat messages and predicts diabetes risk
"""

import pickle
import re
import numpy as np
from typing import Dict, Optional, Tuple
import os

class DiabetesDetector:
    """Detects diabetes risk based on symptoms and medical values from chat"""
    
    def __init__(self, model_path: str = './diabetes.pkl'):
        """Initialize the diabetes detector with the trained model"""
        self.model = None
        self.model_path = model_path
        self.feature_names = [
            'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
        ]
        self.load_model()
    
    def load_model(self):
        """Load the trained diabetes prediction model"""
        try:
            if os.path.exists(self.model_path):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    with open(self.model_path, 'rb') as f:
                        # Try to load with compatibility mode
                        try:
                            self.model = pickle.load(f)
                            print(f"✅ Diabetes model loaded from {self.model_path}")
                        except (ValueError, TypeError) as e:
                            # If there's a version incompatibility, try to work around it
                            print(f"⚠️  Model version incompatibility detected. Attempting compatibility mode...")
                            # Try loading with joblib if available (better compatibility)
                            try:
                                import joblib
                                self.model = joblib.load(self.model_path)
                                print(f"✅ Diabetes model loaded using joblib from {self.model_path}")
                            except:
                                # If all else fails, we'll use a simple rule-based approach
                                print(f"⚠️  Could not load model. Using rule-based assessment.")
                                self.model = None
            else:
                print(f"⚠️  Diabetes model not found at {self.model_path}")
        except Exception as e:
            print(f"⚠️  Error loading diabetes model: {e}. Using rule-based assessment.")
            self.model = None
    
    def extract_number(self, text: str, pattern: str) -> Optional[float]:
        """Extract a number from text using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        return None
    
    def extract_glucose(self, text: str) -> Optional[float]:
        """Extract blood glucose level from text"""
        patterns = [
            r'glucose[:\s]+is[:\s]+(\d+(?:\.\d+)?)',
            r'glucose[:\s]+(\d+(?:\.\d+)?)',
            r'blood sugar[:\s]+is[:\s]+(\d+(?:\.\d+)?)',
            r'blood sugar[:\s]+(\d+(?:\.\d+)?)',
            r'sugar level[:\s]+is[:\s]+(\d+(?:\.\d+)?)',
            r'sugar level[:\s]+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*mg/dl',
            r'glucose is (\d+(?:\.\d+)?)',
            r'glucose of (\d+(?:\.\d+)?)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 50 <= value <= 500:  # Reasonable glucose range
                return value
        return None
    
    def extract_bp(self, text: str) -> Optional[float]:
        """Extract blood pressure from text"""
        patterns = [
            r'blood pressure[:\s]+(\d+)',
            r'bp[:\s]+(\d+)',
            r'(\d+)\s*/\s*\d+\s*mmhg',
            r'pressure is (\d+)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 50 <= value <= 200:  # Reasonable BP range
                return value
        return None
    
    def extract_bmi(self, text: str) -> Optional[float]:
        """Extract BMI from text"""
        patterns = [
            r'bmi[:\s]+is[:\s]+(\d+(?:\.\d+)?)',
            r'bmi[:\s]+(\d+(?:\.\d+)?)',
            r'body mass index[:\s]+is[:\s]+(\d+(?:\.\d+)?)',
            r'body mass index[:\s]+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*bmi',
            r'bmi of (\d+(?:\.\d+)?)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 10 <= value <= 50:  # Reasonable BMI range
                return value
        return None
    
    def extract_age(self, text: str) -> Optional[float]:
        """Extract age from text"""
        patterns = [
            r'age[:\s]+is[:\s]+(\d+)',
            r'age[:\s]+(\d+)',
            r'(\d+)\s*years?\s*old',
            r'i am (\d+)',
            r'i\'m (\d+)',
            r'aged (\d+)',
            r'age of (\d+)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 1 <= value <= 120:  # Reasonable age range
                return value
        return None
    
    def extract_pregnancies(self, text: str) -> Optional[float]:
        """Extract number of pregnancies from text"""
        patterns = [
            r'pregnanc(?:y|ies)[:\s]+(\d+)',
            r'(\d+)\s*pregnanc(?:y|ies)',
            r'given birth (\d+)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 0 <= value <= 20:  # Reasonable range
                return value
        return None
    
    def extract_insulin(self, text: str) -> Optional[float]:
        """Extract insulin level from text"""
        patterns = [
            r'insulin[:\s]+(\d+(?:\.\d+)?)',
            r'insulin level[:\s]+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*mu/l',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 0 <= value <= 1000:  # Reasonable insulin range
                return value
        return None
    
    def extract_skin_thickness(self, text: str) -> Optional[float]:
        """Extract skin thickness (triceps) from text"""
        patterns = [
            r'skin thickness[:\s]+(\d+(?:\.\d+)?)',
            r'triceps[:\s]+(\d+(?:\.\d+)?)',
            r'thickness[:\s]+(\d+(?:\.\d+)?)',
        ]
        for pattern in patterns:
            value = self.extract_number(text, pattern)
            if value and 0 <= value <= 100:  # Reasonable range
                return value
        return None
    
    def extract_diabetes_pedigree(self, text: str) -> Optional[float]:
        """Extract diabetes pedigree function from text"""
        # This is harder to extract from natural language, use default or estimate
        # Check for family history keywords
        family_keywords = ['family history', 'parent', 'mother', 'father', 'sibling', 'diabetes in family']
        if any(keyword in text.lower() for keyword in family_keywords):
            # Return a moderate value if family history exists
            return 0.5
        return None
    
    def extract_features_from_text(self, text: str, conversation_history: list = None) -> Dict[str, Optional[float]]:
        """Extract all features from text and conversation history"""
        # Combine current text with conversation history
        full_text = text.lower()
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                    if content:
                        full_text += ' ' + content.lower()
                elif isinstance(msg, str):
                    full_text += ' ' + msg.lower()
        
        features = {
            'Pregnancies': self.extract_pregnancies(full_text),
            'Glucose': self.extract_glucose(full_text),
            'BloodPressure': self.extract_bp(full_text),
            'SkinThickness': self.extract_skin_thickness(full_text),
            'Insulin': self.extract_insulin(full_text),
            'BMI': self.extract_bmi(full_text),
            'DiabetesPedigreeFunction': self.extract_diabetes_pedigree(full_text),
            'Age': self.extract_age(full_text),
        }
        
        return features
    
    def get_default_values(self) -> Dict[str, float]:
        """Get default/median values for missing features"""
        # Based on typical diabetes dataset medians
        return {
            'Pregnancies': 3.0,
            'Glucose': 120.0,
            'BloodPressure': 72.0,
            'SkinThickness': 23.0,
            'Insulin': 30.5,
            'BMI': 32.0,
            'DiabetesPedigreeFunction': 0.3725,
            'Age': 29.0,
        }
    
    def rule_based_assessment(self, features: Dict[str, Optional[float]]) -> Tuple[bool, float]:
        """Rule-based diabetes risk assessment when model is unavailable"""
        risk_score = 0.0
        risk_factors = 0
        
        # Check glucose level
        glucose = features.get('Glucose')
        if glucose:
            if glucose >= 200:
                risk_score += 0.4
                risk_factors += 1
            elif glucose >= 140:
                risk_score += 0.3
                risk_factors += 1
            elif glucose >= 100:
                risk_score += 0.1
        
        # Check BMI
        bmi = features.get('BMI')
        if bmi:
            if bmi >= 30:
                risk_score += 0.2
                risk_factors += 1
            elif bmi >= 25:
                risk_score += 0.1
        
        # Check age
        age = features.get('Age')
        if age and age >= 45:
            risk_score += 0.1
            risk_factors += 1
        
        # Check blood pressure
        bp = features.get('BloodPressure')
        if bp and bp >= 140:
            risk_score += 0.1
            risk_factors += 1
        
        # Family history
        if features.get('DiabetesPedigreeFunction'):
            risk_score += 0.1
            risk_factors += 1
        
        # Normalize probability (ensure it's between 0.1 and 0.95)
        if risk_factors > 0:
            probability = min(max(risk_score, 0.1), 0.95)
        else:
            probability = 0.15  # Default low risk
        
        has_risk = probability >= 0.3
        
        return has_risk, probability
    
    def predict(self, text: str, conversation_history: list = None) -> Tuple[bool, float, Dict[str, Optional[float]], str]:
        """
        Predict diabetes risk from text
        
        Returns:
            (has_risk, probability, extracted_features, message)
        """
        # Extract features from text
        features = self.extract_features_from_text(text, conversation_history)
        default_values = self.get_default_values()
        
        # Count how many features we extracted
        extracted_count = sum(1 for v in features.values() if v is not None)
        
        # Use extracted values or defaults
        feature_array = np.array([
            features.get('Pregnancies') or default_values['Pregnancies'],
            features.get('Glucose') or default_values['Glucose'],
            features.get('BloodPressure') or default_values['BloodPressure'],
            features.get('SkinThickness') or default_values['SkinThickness'],
            features.get('Insulin') or default_values['Insulin'],
            features.get('BMI') or default_values['BMI'],
            features.get('DiabetesPedigreeFunction') or default_values['DiabetesPedigreeFunction'],
            features.get('Age') or default_values['Age'],
        ]).reshape(1, -1)
        
        # Make prediction
        try:
            if self.model:
                prediction = self.model.predict(feature_array)[0]
                probability = self.model.predict_proba(feature_array)[0][1] if hasattr(self.model, 'predict_proba') else 0.5
                has_risk = bool(prediction == 1)
            else:
                # Use rule-based assessment
                has_risk, probability = self.rule_based_assessment(features)
            
            # Generate message
            if extracted_count < 3:
                message = f"⚠️ Limited information available. Based on {extracted_count} extracted values, "
            else:
                message = f"Based on {extracted_count} extracted medical values, "
            
            if has_risk:
                message += f"there is a {probability*100:.1f}% risk of diabetes. Please consult a healthcare professional for proper diagnosis."
            else:
                message += f"the diabetes risk appears low ({probability*100:.1f}%). However, please consult a healthcare professional for accurate assessment."
            
            return has_risk, float(probability), features, message
            
        except Exception as e:
            # Fallback to rule-based if model prediction fails
            has_risk, probability = self.rule_based_assessment(features)
            extracted_count = sum(1 for v in features.values() if v is not None)
            if extracted_count < 3:
                message = f"⚠️ Limited information available. Based on {extracted_count} extracted values, diabetes risk assessment: {probability*100:.1f}% risk. Please consult a healthcare professional for accurate diagnosis."
            else:
                message = f"Based on {extracted_count} extracted values, diabetes risk assessment: {probability*100:.1f}% risk. Please consult a healthcare professional for accurate diagnosis."
            return has_risk, float(probability), features, message

# Global instance
_diabetes_detector = None

def get_diabetes_detector() -> DiabetesDetector:
    """Get or create the global diabetes detector instance"""
    global _diabetes_detector
    if _diabetes_detector is None:
        _diabetes_detector = DiabetesDetector()
    return _diabetes_detector

def detect_diabetes_from_chat(text: str, conversation_history: list = None) -> Dict:
    """
    Detect diabetes risk from chat message
    
    Returns:
        {
            'has_risk': bool,
            'probability': float,
            'features': dict,
            'message': str,
            'success': bool
        }
    """
    try:
        detector = get_diabetes_detector()
        has_risk, probability, features, message = detector.predict(text, conversation_history)
        
        return {
            'has_risk': has_risk,
            'probability': probability,
            'features': features,
            'message': message,
            'success': True
        }
    except Exception as e:
        return {
            'has_risk': False,
            'probability': 0.0,
            'features': {},
            'message': f"Error in diabetes detection: {str(e)}",
            'success': False
        }

