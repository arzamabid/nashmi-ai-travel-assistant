
def merge_parameters(
    previous: dict | None,
    new: dict,
) -> dict:
    result = dict(previous or {})

    for key, value in new.items():
        if value is not None:
            result[key] = value

    return result
