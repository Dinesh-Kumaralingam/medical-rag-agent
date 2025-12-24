import pandas as pd

# Test Cost Logic
def calculate_cost(base_avg_cost, severity):
    if severity == "Mild":
        return base_avg_cost / 20, "Urgent Care Visit"
    elif severity == "Moderate":
        return base_avg_cost / 5, "Specialist Visit"
    else: # Severe/Emergency
        return base_avg_cost, "Hospital Admission"

try:
    print("Loading data...")
    healthcare_df = pd.read_csv("optimized_healthcare_data.csv")
    print("Data loaded.")

    # Pick a condition to test
    condition = "Asthma"
    condition_data = healthcare_df[healthcare_df['Medical Condition'] == condition]
    
    if not condition_data.empty:
        base_avg_cost = condition_data['Billing Amount'].mean()
        print(f"\nBase Avg Cost for {condition}: ${base_avg_cost:,.2f}")
        
        # Test Scenarios
        scenarios = ["Mild", "Moderate", "Severe", "Emergency"]
        for sev in scenarios:
            cost, visit_type = calculate_cost(base_avg_cost, sev)
            print(f"Severity: {sev} -> Cost: ${cost:,.2f} ({visit_type})")
            
            # Assertions
            if sev == "Mild":
                assert cost == base_avg_cost / 20
            elif sev == "Moderate":
                assert cost == base_avg_cost / 5
            else:
                assert cost == base_avg_cost
        
        print("\nCost Logic Verified Successfully.")
    else:
        print(f"Condition {condition} not found in data.")

except Exception as e:
    print(f"Error in logic: {e}")
