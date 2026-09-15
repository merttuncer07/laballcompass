import json
from tfld import design_localization

def main():
    lengths=[16,32,64,128,256,512]
    feasible=design_localization(sample_rate_hz=1000,maximum_time_spread_seconds=.02,maximum_frequency_spread_hz=10,window_lengths=lengths)
    impossible=design_localization(sample_rate_hz=1000,maximum_time_spread_seconds=.002,maximum_frequency_spread_hz=5,window_lengths=lengths)
    print(json.dumps({"feasible":feasible.to_dict(),"impossible_closest":impossible.to_dict()},indent=2))
if __name__=="__main__": main()
