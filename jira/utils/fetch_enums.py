def fetch_enums(jira, endpoint = 'issuetype', filter = None, mapping = {}, caster_functions = {}):
    """Get the enums of the fields in a jira tenant

    Args:
        jira (_type_): Client for connecting to the endpoint.
        endpoint (str, optional): The endpoint for the specific field. Defaults to 'issuetype'.
        filter (_type_, optional): Filters the return value if set. Defaults to None.
        mapping (dict, optional): Renames an internal field name in the Jira api to something custom. Defaults to {}.
        caster_functions (dict, optional): Casts fields using custom conversion functions. Defaults to {}.

    Returns:
        _type_: _description_
    
    Example for /rest/api/2/issuetype:
        types_filter = lambda d: int(d['id']) < 100 and d['name'] in ('Bug', 'Task', 'Epic', 'Story', 'Incident', 'New Feature', 'Sub-Task')
        mapping = {'id': 'id', 'description': 'description', 'untranslatedName': 'name'}
        caster_functions = {'id': int}
        issue_enums = fetch_enums(jira, endpoint = 'issuetype', filter = types_filter, mapping = mapping, caster_functions = caster_functions)
    
    See https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-types/#api-rest-api-2-issuetype-get
    """
    response = jira._get(f'/{endpoint}')
    response.raise_for_status()
    data = response.json()
    schemas = []
    for entry in data:
        schema = {}
        for api_name, rename in mapping.items():
            cast = caster_functions.get(rename, lambda unchanged: unchanged)
            api_value = cast(entry.get(api_name))
            schema[rename] = api_value
        if filter and filter(schema):
            schemas.append(schema)
    return schemas