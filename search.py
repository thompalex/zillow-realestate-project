import re

class Limit:
    def __init__(self, **kwargs):
        self.keys = set(kwargs.keys())
        self.search_param = {}
        for key, item in kwargs.items():
            self.search_param[key] = Feature(name = item['name'], data = item['data'], error =  item['error'])
        
    # check if the search is possible
    def check_param(self, param):
        print(self.keys)
        if not set(param.keys()).issubset(self.keys):
            return (None, ["You don't have enough parameter"])
        else:
            errorList = []
            for key, item in param.items():
                value = self.search_param[key]
                if item not in value.get_data().keys():
                    errorList.append(value.get_error())
            return (param, None) if len(errorList) == 0 else (None, errorList)

    def param(self):
        return {key: [value.get_name(), value.get_data()] for key, value in self.search_param.items()}

    
class Feature:
    def __init__(self, name, data, error):
        self.name = name
        self.data = data
        self.error = error

    def get_name(self):
        return self.name

    def get_data(self):
        return self.data

    def get_error(self):
        return self.error        