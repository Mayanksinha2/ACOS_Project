from dataclasses import asdict
import json


class ACNPSerializer:

    @staticmethod
    def serialize(message):

        return json.dumps(asdict(message), indent=4)

    @staticmethod
    def deserialize(data):

        return json.loads(data)