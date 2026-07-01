from craft_text_detector import Craft
import numpy as np

craft = Craft(output_dir="outputs", crop_type="poly", cuda=False)
result = craft.detect_text("dummy.png")
polys = result.get("boxes", [])

print(f"polys type: {type(polys)}")
if len(polys) > 0:
    p = polys[0]
    print(f"p type: {type(p)}")
    print(p)
