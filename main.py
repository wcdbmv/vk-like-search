#!/usr/bin/python3

import requests
import time


class Vk:
    def __init__(self, app_id, access_token, api_version):
        self.app_id = app_id
        self.access_token = access_token
        self.api_version = api_version

        self.api_url = 'https://api.vk.com/method/'
        self.execute_url = self.link('execute')

        self.WALL_GET_LIMIT = 100
        self.EXECUTE_LIMIT = 25
        self.EXECUTE_WALL_GET_LIMIT = self.EXECUTE_LIMIT * self.WALL_GET_LIMIT

    def link(self, method):
        url = self.api_url + method + '?access_token=' + self.access_token + '&v=' + self.api_version
        return url

    @staticmethod
    def response_get(url, params=None):
        response = requests.get(url, params=params).json()
        if 'response' in response:
            return response['response']
        return response['error']

    def execute_wall_get(self, owner_id, offset=0):
        response = self.response_get(self.execute_url, params={'code': '''
            var response = API.wall.get({{owner_id: {owner_id}, count: {wall_get_limit}}});
            var item_ids = response.items@.id;

            var offset = {wall_get_limit} + {offset};
            while (offset < {execute_wall_get_limit} + {offset}) {{
                item_ids = item_ids + API.wall.get({{
                    owner_id: {owner_id},
                    offset: offset,
                    count: {wall_get_limit}}}).items@.id;
                offset = offset + {wall_get_limit};
            }}

            response.items = item_ids;

            return(response);
        '''.format(
            owner_id=owner_id,
            offset=offset,
            wall_get_limit=self.WALL_GET_LIMIT,
            execute_limit=self.EXECUTE_LIMIT,
            execute_wall_get_limit=self.EXECUTE_WALL_GET_LIMIT
        )})
        if 'count' not in response:
            print(response)
        return response['count'], response['items']

    def wall_get(self, owner_id, count=None):
        if count is None:
            count, item_ids = self.execute_wall_get(owner_id)
            start = self.EXECUTE_WALL_GET_LIMIT
        else:
            item_ids = list()
            start = 0

        for offset in range(start, count, self.EXECUTE_WALL_GET_LIMIT):
            item_ids += self.execute_wall_get(owner_id, offset)[1]
            print('{:5} received'.format(len(item_ids)))
            time.sleep(0.34)

        return count, item_ids

    def execute_likes_is_liked(self, user_id, owner_id, item_ids):
        response = self.response_get(self.execute_url, params={'code': '''
            var items = {item_ids},
                liked = [];

            var i = 0;
            while (i < {execute_limit}) {{
                if (API.likes.isLiked({{
                    user_id: {user_id},
                    type: "post",
                    owner_id: {owner_id},
                    item_id: items[i]
                }}).liked)
                    liked = liked + [items[i]];
                i = i + 1;
            }}

            return(liked);
        '''.format(
            user_id=user_id,
            owner_id=owner_id,
            item_ids=item_ids,
            execute_limit=self.EXECUTE_LIMIT
        )})
        return response

    def likes_is_liked(self, user_id, owner_id, item_ids):
        liked, offset = list(), 0
        while offset < len(item_ids):
            next_offset = offset + self.EXECUTE_LIMIT
            liked += self.execute_likes_is_liked(user_id, owner_id, item_ids[offset:next_offset])
            offset = next_offset
            print('{:5d}/{} processed, {:4d} liked'.format(offset, len(item_ids), len(liked)))
            time.sleep(0.34)
        return liked


class LikeSearch:
    def __init__(self, vk, targets=list()):
        self.vk = vk
        self.targets = targets

    def search_for(self, user_id, owner_id):
        print('user_id: {}, owner_id: {}'.format(user_id, owner_id))

        count, item_ids = self.vk.wall_get(owner_id)
        print('count: {}'.format(count))

        liked = self.vk.likes_is_liked(user_id, owner_id, item_ids)

        with open('{}_{}_{}'.format(user_id, owner_id, time.strftime("%Y%m%d%H%M%S")), 'w') as file:
            for post_id in liked:
                url = 'https://vk.com/wall{}_{}\n'.format(owner_id, post_id)
                file.write('[{0}]({0})<br>\n'.format(url))

    def search(self):
        if not self.targets:
            return

        for user_id, owner_ids in self.targets:
            for owner_id in owner_ids:
                self.search_for(user_id, owner_id)


def main():
    like_search = LikeSearch(
        Vk(
            app_id='',
            access_token='',
            api_version=''
        ),
        targets=[
            [0, []]
        ]
    )

    like_search.search()


if __name__ == '__main__':
    main()
