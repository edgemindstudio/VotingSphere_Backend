# voting/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.election_id = self.scope['url_route']['kwargs']['election_id']
        self.room_group_name = f"election_{self.election_id}"

        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def vote_update(self, event):
        # Send vote update to WebSocket
        await self.send(text_data=json.dumps({
            'candidate_id': event['data']['candidate_id'],
            'total_votes': event['data']['total_votes']
        }))
