"""
Web version of the Pain Score Calculator using Streamlit
Using joblib for better version compatibility

Run with: streamlit run app_compatible.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import joblib  # Use joblib instead of pickle for better compatibility

# Set up page
st.set_page_config(
    page_title="Hip Replacement Pain Predictor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
T3_IMPORTANT_FEATURES = [
    'LOS', 'BMI_Current', 'WOMACP_5', 'WeightCurrent', 'ICOAPC_3',
    'ICOAPC_1', 'AgePreOp', 'WOMACP_3', 'WalkPain', 'MobilityAidWalker',
    'Pre-Op Pain', 'HeightCurrent', 'ResultsRelief'
]

T5_IMPORTANT_FEATURES = [
    'AgePreOp', 'BMI_Current', 'WeightCurrent', 'HeightCurrent', 'LOS',
    'WOMACP_5', 'ResultsRelief', 'ICOAPC_3', 'Pre-Op Pain', 'WalkPain',
    'Approach', 'HeadSize'
]

MODELS_DIR = 'streamlit_models'  # Change to the new directory name

def get_feature_descriptions():
    """Return descriptions for the features used in the models"""
    feature_descriptions = {
        'LOS': 'Legth of stay (days)',
        'BMI_Current': 'Body Mass Index',
        'WOMACP_5': ' Pain Standing upright (0-4)',
        'WeightCurrent': 'Current weight (kg)',
        'ICOAPC_3': 'In the past week, how much has your constant hip pain affected your overall quality of life (0-4)',
        'ICOAPC_1': 'In the past week, how intense has your constant hip pain been? (0-4)',
        'AgePreOp': 'Age at pre-op (years)',
        'WOMACP_3': 'Pain At night while in bed (0-4)',
        'WalkPain': 'Pain while walking (0-10)',
        'MobilityAidWalker': 'Uses walker as mobility aid',
        'Pre-Op Pain': 'Pre-operation pain score (0-10)',
        'HeightCurrent': 'Current height (cm)',
        'ResultsRelief': 'Expected relief result (1-5)',
        'Approach': 'Surgical approach (e.g., "Posterior", "Anterior")',
        'HeadSize': 'Size of the femoral head implant (mm)'
    }
    return feature_descriptions

def load_models(timepoint):
    """Load saved models and preprocessors using joblib"""
    model_path = os.path.join(MODELS_DIR, f'{timepoint.lower()}_model.joblib')
    preprocessor_path = os.path.join(MODELS_DIR, f'{timepoint.lower()}_preprocessor.joblib')
    
    if not (os.path.exists(model_path) and os.path.exists(preprocessor_path)):
        raise FileNotFoundError(
            f"Pre-trained models not found in '{MODELS_DIR}' directory. "
            f"Please run 'train_models_compatible.py' first to create the models."
        )
    
    # Load model and preprocessor using joblib
    model = joblib.load(model_path)
    preprocessor = joblib.load(preprocessor_path)
    
    return model, preprocessor

def predict_with_model(patient_data, timepoint='T3'):
    """
    Predict pain score for a patient using the specified timepoint model.
    
    Parameters:
    -----------
    patient_data : dict
        Dictionary containing patient features
    timepoint : str, optional (default='T3')
        Timepoint for which to predict pain ('T3' or 'T5')
    
    Returns:
    --------
    float
        Predicted pain score
    """
    # Ensure timepoint is uppercase
    timepoint = timepoint.upper()
    if timepoint not in ['T3', 'T5']:
        raise ValueError("Timepoint must be 'T3' or 'T5'")
    
    # Load model and preprocessor
    model, preprocessor = load_models(timepoint)
    
    # Determine required features
    required_features = T3_IMPORTANT_FEATURES if timepoint == 'T3' else T5_IMPORTANT_FEATURES
    
    # Check that all required features are provided
    missing_features = [f for f in required_features if f not in patient_data]
    if missing_features:
        raise ValueError(f"Missing required features: {missing_features}")
    
    # Create DataFrame from patient data
    patient_df = pd.DataFrame([patient_data])
    
    # Convert HeadSize to string if present
    if 'HeadSize' in patient_df.columns:
        patient_df['HeadSize'] = patient_df['HeadSize'].astype(str)
    
    # Preprocess the patient data
    patient_processed = preprocessor.transform(patient_df)
    
    # Make prediction
    prediction = model.predict(patient_processed)[0]
    
    # Clip prediction to valid range [0, 8]
    prediction = np.clip(prediction, 0, 8)
    
    return prediction

def predict_in_demo_mode(patient_data, timepoint):
    """Generate a simulated prediction for demo mode"""
    # Simple simulation logic based on input values
    if timepoint == "T3":
        # Create a simple formula for demonstration
        bmi_factor = 0.01 * patient_data.get('BMI_Current', 25)
        age_factor = 0.01 * patient_data.get('AgePreOp', 65)
        preop_factor = 0.2 * patient_data.get('Pre-Op Pain', 5)
        walk_factor = 0.1 * patient_data.get('WalkPain', 5)
        
        prediction = 2.0 + bmi_factor + age_factor + preop_factor - walk_factor
        prediction = max(0, min(8, prediction))  # Ensure between 0-8
    else:
        # Different formula for T5
        bmi_factor = 0.008 * patient_data.get('BMI_Current', 25)
        age_factor = 0.005 * patient_data.get('AgePreOp', 65)
        preop_factor = 0.15 * patient_data.get('Pre-Op Pain', 5)
        approach_factor = 0.5 if patient_data.get('Approach') == 'Posterior' else 0
        
        prediction = 1.5 + bmi_factor + age_factor + preop_factor - approach_factor
        prediction = max(0, min(8, prediction))  # Ensure between 0-8
    
    return prediction

def check_models_exist():
    """Check if pre-trained models exist"""
    model_files = [
        os.path.join(MODELS_DIR, 't3_model.joblib'),
        os.path.join(MODELS_DIR, 't3_preprocessor.joblib'),
        os.path.join(MODELS_DIR, 't5_model.joblib'),
        os.path.join(MODELS_DIR, 't5_preprocessor.joblib')
    ]
    
    return all(os.path.exists(f) for f in model_files)

def main():
    st.title("Hip Replacement Pain Predictor")
    st.markdown("""
    This tool predicts post-operative pain scores for hip replacement patients at two timepoints:
    * **T3**: 3 years post-operation
    * **T5**: 5 years post-operation
    
    **Note**: This calculator is based on statistical models and should be used only as a reference. 
    Actual patient outcomes may vary.
    """)
    
    # Check if models directory exists
    if not os.path.exists(MODELS_DIR):
        st.warning(f"Models directory '{MODELS_DIR}' not found. Using demo mode.")
        use_demo_mode = True
    else:
        # Check if models exist
        use_demo_mode = not check_models_exist()
        if use_demo_mode:
            st.warning("Pre-trained models not found. Using demo mode.")
    
    # Sidebar
    st.sidebar.title("Pain Score Prediction")
    timepoint = st.sidebar.radio("Select timepoint to predict:", ["T3 (3 years)", "T5 (5 years)"])
    
    # Remove parentheses from timepoint string
    timepoint_code = timepoint.split(" ")[0]
    
    st.header(f"Patient Information for {timepoint}")
    
    # Get required features based on timepoint
    required_features = T3_IMPORTANT_FEATURES if timepoint_code == "T3" else T5_IMPORTANT_FEATURES
    feature_descriptions = get_feature_descriptions()
    
    # Use columns to organize the layout
    col1, col2 = st.columns(2)
    
    # Initialize patient data dictionary
    patient_data = {}
    
    # Create input fields for required features
    for i, feature in enumerate(required_features):
        description = feature_descriptions.get(feature, "")
        
        # Decide which column to put the feature in (alternate between columns)
        current_col = col1 if i % 2 == 0 else col2
        
        with current_col:
            if feature == 'MobilityAidWalker':
                patient_data[feature] = int(st.selectbox(
                    f"{feature} ({description})",
                    options=[0, 1],
                    format_func=lambda x: "No" if x == 0 else "Yes"
                ))
            elif feature == 'Approach':
                patient_data[feature] = st.selectbox(
                    f"{feature} ({description})",
                    options=["Posterior", "Anterior", "Lateral", "Other"]
                )
            elif feature in ['WOMACP_5', 'WOMACP_3', 'ICOAPC_3', 'ICOAPC_1']:
                # WOMAC and ICOA scores are on 0-4 scale
                patient_data[feature] = st.slider(
                    f"{feature} ({description})",
                    min_value=0,
                    max_value=4,
                    step=1
                )
            elif feature == 'ResultsRelief':
                # ResultsRelief is on 1-5 scale
                patient_data[feature] = st.slider(
                    f"{feature} ({description})",
                    min_value=1,
                    max_value=5,
                    step=1
                )
            elif feature == 'WalkPain' or feature == 'Pre-Op Pain':
                # Pain scores are on 0-10 scale
                patient_data[feature] = st.slider(
                    f"{feature} ({description})",
                    min_value=0,
                    max_value=10,
                    step=1
                )
            elif feature == 'HeadSize':
                # HeadSize is typically 28, 32, or 36 mm
                patient_data[feature] = st.selectbox(
                    f"{feature} ({description})",
                    options=["28", "32", "36", "40", "Other"]
                )
            else:
                # Default numeric input for other fields
                patient_data[feature] = st.number_input(
                    f"{feature} ({description})",
                    value=0.0,
                    step=0.1
                )
    
    # Predict button
    if st.button("Predict Pain Score"):
        try:
            # Try to use the trained model first, fall back to demo mode if it fails
            if use_demo_mode:
                prediction = predict_in_demo_mode(patient_data, timepoint_code)
                st.info("Using demo mode: predictions are approximate and not based on trained models")
            else:
                try:
                    prediction = predict_with_model(patient_data, timepoint_code)
                except Exception as e:
                    st.warning(f"Error using trained model: {str(e)}. Falling back to demo mode.")
                    prediction = predict_in_demo_mode(patient_data, timepoint_code)
                    st.info("Using demo mode: predictions are approximate and not based on trained models")
            
            # Display results
            st.header("Prediction Results")
            
            # Create a gauge-chart-like display
            fig, ax = plt.subplots(figsize=(10, 2))
            
            # Create a color gradient for the gauge
            cmap = plt.cm.RdYlGn_r  # Red-Yellow-Green reversed (red is high pain)
            
            # Background bar (grey)
            ax.barh(0, 8, color='lightgrey', alpha=0.3)
            
            # Colored bar based on prediction
            ax.barh(0, prediction, color=cmap(prediction/8))
            
            # Customize appearance
            ax.set_xlim(0, 8)
            ax.set_yticks([])
            ax.set_xticks([0, 2, 4, 6, 8])
            ax.set_xticklabels(['0\nNo Pain', '2', '4', '6', '8\nExtreme Pain'])
            
            # Add marker for the prediction
            ax.plot(prediction, 0, 'ko', markersize=12)
            ax.text(prediction, 0, f'{prediction:.1f}', ha='center', va='bottom', fontsize=14, fontweight='bold')
            
            # Remove y-axis
            ax.spines['left'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            
            # Display the plot
            st.pyplot(fig)
            
            # Interpret the prediction
            if prediction <= 2:
                interpretation = "minimal"
                color = "green"
            elif prediction <= 4:
                interpretation = "mild"
                color = "blue"
            elif prediction <= 6:
                interpretation = "moderate"
                color = "orange"
            else:
                interpretation = "severe"
                color = "red"
            
            st.markdown(f"<h3 style='color:{color}'>Predicted pain level: <b>{interpretation}</b></h3>", unsafe_allow_html=True)
            
            # Additional interpretation
            st.markdown(f"""
            This prediction suggests a **{interpretation}** pain level ({prediction:.1f}/8) at {timepoint}.
            """)
            
        except Exception as e:
            st.error(f"Error making prediction: {str(e)}")

if __name__ == "__main__":
    main()
