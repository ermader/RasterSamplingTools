# Output Database
`OutputDatabase.json` is a JSON format file written by the `rastersamplingtest` tool. It is a single JSON object where the field names are the postscript names of fonts. The value of each field is a JSON object with a single field named *test_results*, whose value is a *test_results* object.

The test_results object is a JSON object where the name of each field is the name of a glyph that was tested. The glyph names are in *glyphSpec* format - e.g. "/l.ss01". The value of the field is a *glyph test_results* object.

## Glyph test_results Object
* **contour_count** : the number of coutours in the glyph
* **width_method** : the width method used to test the glyph
* **main_contour** : the method used to select the main contour of the glyph
* **direction** : the direction of the glyph
* **main_contour_area_percent** : the percentage the area of the main contour is of the overall area of the glyph
* **main_contour_height_percent** : the percentage the height of the main contour is of the overall height of the glyph
* **chosen_width_method** : the width method used to analyze the glyph
* **raster_sample_range** : the range over which the raster samples are made
* **fit_results** : a JSON object containing the results of calling `scipy.stats.linregress` on the midpoints of the lines where the rasters intersect the selected stroke
* **widths** : a JSON object containing the `statistics.quantiles` of the stroke widths

## fit_results Object
* **slope** : the slope of the line fitted through the midpoints of the midpoints of the lines where the rasters intersect the selected stroke
* **intercept** : the coordinate where the fitted line intersects the axis
* **r_squared** : the square of the r-value of the fitted line
* **std_err** : the standard error of the fit
* **stroke_angle** : the computed angle of the stroke, in degrees

## widths Object
* **min** : the minimum stroke width
* **q1** : the firat quartile of the stroke widths
* **median** : the median stroke width (also the second quartile)
* **mean** : the mean stroke width
* **q3** : the third quartile of the stroke widths
* **max** : the maximum stroke width

### Example
    {
        ...
        "HelveticaNeue-Italic": {
            "test_results": {
                "/l": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "0-96",
                    "fit_results": {
                        "slope": 0.2094,
                        "intercept": 38.0,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.8
                    },
                    "widths": {
                        "min": 84.0,
                        "q1": 84.24,
                        "median": 84.47,
                        "mean": 84.47,
                        "q3": 84.71,
                        "max": 84.94
                    }
                },
                "/j": {
                    "contour_count": 2,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 68.943,
                    "main_contour_height_percent": 78.375,
                    "chosen_width_method": "left",
                    "raster_sample_range": "8-72",
                    "fit_results": {
                        "slope": 0.2118,
                        "intercept": 36.57,
                        "r_squared": 0.9994,
                        "std_err": 0.0009,
                        "stroke_angle": 12.0
                    },
                    "widths": {
                        "min": 82.1,
                        "q1": 82.69,
                        "median": 83.37,
                        "mean": 83.66,
                        "q3": 84.15,
                        "max": 91.49
                    }
                },
                "/I": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "0-96",
                    "fit_results": {
                        "slope": 0.2101,
                        "intercept": 54.5,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.9
                    },
                    "widths": {
                        "min": 95.0,
                        "q1": 95.0,
                        "median": 95.0,
                        "mean": 95.0,
                        "q3": 95.0,
                        "max": 95.0
                    }
                },
                "/L": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "12-96",
                    "fit_results": {
                        "slope": 0.2091,
                        "intercept": 55.17,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.8
                    },
                    "widths": {
                        "min": 95.08,
                        "q1": 95.36,
                        "median": 95.63,
                        "mean": 95.63,
                        "q3": 95.91,
                        "max": 96.19
                    }
                },
                "/afii10020": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "0-86",
                    "fit_results": {
                        "slope": 0.2114,
                        "intercept": 55.5,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.9
                    },
                    "widths": {
                        "min": 94.92,
                        "q1": 94.94,
                        "median": 94.96,
                        "mean": 94.96,
                        "q3": 94.98,
                        "max": 95.0
                    }
                },
                "/afii10036": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "0-86",
                    "fit_results": {
                        "slope": 0.2114,
                        "intercept": 213.5,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.9
                    },
                    "widths": {
                        "min": 95.0,
                        "q1": 95.0,
                        "median": 95.0,
                        "mean": 95.0,
                        "q3": 95.0,
                        "max": 95.0
                    }
                },
                "/uni04C0": {
                    "contour_count": 1,
                    "width_method": "leastspread",
                    "main_contour": "tallest",
                    "direction": "ltr",
                    "main_contour_area_percent": 100.0,
                    "main_contour_height_percent": 100.0,
                    "chosen_width_method": "left",
                    "raster_sample_range": "0-96",
                    "fit_results": {
                        "slope": 0.2101,
                        "intercept": 54.5,
                        "r_squared": 1.0,
                        "std_err": 0.0,
                        "stroke_angle": 11.9
                    },
                    "widths": {
                        "min": 95.0,
                        "q1": 95.0,
                        "median": 95.0,
                        "mean": 95.0,
                        "q3": 95.0,
                        "max": 95.0
                    }
                }
            }
        },
        ...
    }