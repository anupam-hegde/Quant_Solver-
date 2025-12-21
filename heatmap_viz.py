import matplotlib.pyplot as plt

def create_mock_heatmap():
    # Mock data based on what Orchestrator stats would look like
    categories = ['Success', 'Hallucination', 'Consensus Fail', 'Parse Error']
    values = [12, 5, 3, 2] # Example counts
    
    colors = ['green', 'red', 'orange', 'gray']
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(categories, values, color=colors)
    
    plt.title('Agent System Performance Heatmap')
    plt.ylabel('Number of Questions')
    plt.grid(axis='y', alpha=0.3)
    
    # Save the plot
    plt.savefig('error_heatmap.png')
    print("✅ Heatmap saved to 'error_heatmap.png'")

if __name__ == "__main__":
    create_mock_heatmap()
