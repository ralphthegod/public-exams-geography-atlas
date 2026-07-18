SOURCE_OPTIMIZATION = {
    "countries": (0.025, {"ADMIN", "NAME", "name", "CONTINENT", "continent", "LABEL_X", "LABEL_Y", "_label"}),
    "regions": (0.006, {"reg_name", "name", "LABEL_X", "LABEL_Y", "label_x", "label_y", "_label"}),
    "provinces": (0.003, {"prov_name", "reg_name", "name", "LABEL_X", "LABEL_Y", "label_x", "label_y", "_label"}),
    "rivers": (0.01, {"name", "NAME", "name_it", "NAME_IT", "_label"}),
    "lakes": (0.01, {"name", "NAME", "name_it", "NAME_IT", "_label"}),
    "local_rivers": (0.0012, {"name", "_label"}),
    "local_lakes": (0.0008, {"name", "_label"}),
}
