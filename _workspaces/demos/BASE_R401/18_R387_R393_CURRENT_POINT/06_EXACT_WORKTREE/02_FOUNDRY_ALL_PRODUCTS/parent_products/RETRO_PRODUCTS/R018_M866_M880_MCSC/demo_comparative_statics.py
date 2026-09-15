import json, numpy as np
from mcsc import certify_monotone_comparative_statics
def main():
 a=np.arange(7.); t=np.arange(6.); good=np.array([[th*x-.5*x*x for th in t] for x in a]); bad=good.copy(); bad[6,5]-=20
 print(json.dumps({"certified":certify_monotone_comparative_statics(a,t,good).to_dict(),"broken":certify_monotone_comparative_statics(a,t,bad).to_dict()},indent=2))
if __name__=="__main__":main()
