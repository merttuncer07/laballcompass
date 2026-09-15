import json
from bpisd import design_binary_persuasion

def main():
    result=design_binary_persuasion(prior_state_one=0.3, action_names=["REJECT","ADOPT"],
        receiver_payoffs=[[0,0],[-1.5,1]], sender_payoffs=[[0,0],[1,1]])
    print(json.dumps(result.to_dict(),indent=2))
if __name__=="__main__": main()
