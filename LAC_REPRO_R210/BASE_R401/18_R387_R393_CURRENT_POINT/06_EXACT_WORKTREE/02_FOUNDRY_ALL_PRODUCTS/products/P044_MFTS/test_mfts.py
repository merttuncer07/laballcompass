from .mfts import *
def test_exact_and_manufacturable_separate():
 r=mfts([.5,.5],thickness=1,min_feature=.4); assert r['mathematically_exact'] and r['manufacturable']
def test_feature_flip_does_not_break_math():
 r=mfts([.5,.5],thickness=1,min_feature=.6); assert r['mathematically_exact'] and not r['manufacturable']
def test_margin_exposed(): assert abs(mfts([.5,.5],thickness=1,min_feature=.4)['fabrication_margin']-.1)<1e-12

