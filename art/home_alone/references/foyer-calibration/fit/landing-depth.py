"""Sensitivity check, not a measurement: infer rear corner depth from Marina 5:46.

Reuses the tread correspondences and projection in fit.py. Camera is fitted to
treads ONLY; the rear corner is held out. No Unity or source-image changes.
"""
import json
import numpy as np
from scipy.optimize import minimize_scalar
from fit import fit, project, views, HERE


def depth_for_pixel(camera, fov, pixel):
    def error(z):
        predicted = project([[-.967, 4.452, z]], camera, fov, [1920, 1080])[0]
        return float(np.sum((predicted - pixel) ** 2))
    solve = minimize_scalar(error, bounds=(8.071, 15), method='bounded')
    return float(solve.x - 8.070), float(np.sqrt(solve.fun))


if __name__ == '__main__':
    camera = [0, 4.8, 6, 0, 0, 0]
    pixel = project([[-.967, 4.452, 10.665]], camera, 60, [1920, 1080])[0]
    recovered, error = depth_for_pixel(camera, 60, pixel)
    assert abs(recovered - 2.595) < .0001 and error < .01
    rows = []
    for width in [.75, 1.0]:
        for fov in [40, 60, 80]:
            result = fit(views['landing'], fov, width)
            depth, error = depth_for_pixel(result['camera'], fov, [797, 438])
            rows.append(dict(width_factor=width, fov=fov,
                             tread_rms_px=result['rms_pixel_distance'],
                             inferred_depth_m=depth, corner_residual_px=error,
                             baseline_corner_error_px=result['held_out_error_px']))
    (HERE / 'landing-depth-results.json').write_text(json.dumps(rows, indent=2) + '\n')
    for row in rows:
        print(json.dumps({k: round(v, 3) for k, v in row.items()}))
