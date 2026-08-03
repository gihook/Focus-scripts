#!/usr/bin/env python3

def extract_type_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "typeId":
                props = ctrl.get("props", {})
                return props.get("options", [])
    return []

def extract_unit_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "unitId":
                props = ctrl.get("props", {})
                return props.get("options", [])
    return []

def extract_quorum_options(create_response):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == "quorum":
                props = ctrl.get("props", {})
                return props.get("options", [])
    return []

def get_control_label(create_response, control_key, default_label):
    form_sections = create_response.get("formSections", [])
    for section in form_sections:
        controls = section.get("formControls", [])
        for ctrl in controls:
            if ctrl.get("key") == control_key:
                props = ctrl.get("props", {})
                return props.get("label", default_label)
    return default_label
