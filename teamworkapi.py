import json
import base64
import re
from functools import partial, update_wrapper

import sys

if sys.version_info[0:2] > (3,0):
    import http.client
    import urllib.parse
else:
    import httplib as http
    http.client = http
    import urllib as urllib
    urllib.parse = urllib



class API(object):
    def __init__(self, *args, **kwargs):
        raise Exception (
                'Please subclass API and override __init__()  to'
                'provide a ConnectionProperties object.'
                )

    def setClient(self, client):
        self.client = client

    def setConnectionProperties(self, props):
        self.client.setConnectionProperties(props)

    def __getattr__(self, key):
        return RequestBuilder(self.client).__getattr__(key)
    __getitem__ = __getattr__

    def __repr__(self):
        return RequestBuilder(self.client).__repr__()

    def getheaders(self):
        return self.client.headers

class TeamWork(API):
    def __init__(self, domain, apikey, *args, **kwargs):
        props = ConnectionProperties(
                    api_url = '{0}.teamwork.com'.format(domain),
                    secure_http = True,
                    extra_headers = {
                        'Authorization': "BASIC " + base64.b64encode(apikey + ":xxx")
                        }
                    )

        self.setClient(Client(*args, **kwargs))
        self.setConnectionProperties(props)

class RequestBuilder(object):
    def __init__(self, client):
        self.client = client
        self.url = ''

    def id(self, id):
        self.url += '/' + str(id)
        return self

    def __getattr__(self, key):
        if key in self.client.http_methods:
            mfun = getattr(self.client, key)
            fun = partial(mfun, url=self.url)
            return update_wrapper(fun, mfun)
        else:
            self.url += '/' + str(key)
            return self

    __getitem__ = __getattr__

    def __str__(self):
        return "I don't know about " + self.url

    def __repr__(self):
        return '%s: %s' % (self.__class__, self.url)

class Client(object):
    http_methods = (
            'head',
            'get',
            'post',
            'put',
            'delete',
            'patch',
            )
    default_headers = {}
    headers = None
    def __init__(self, connection_properties=None):
        if connection_properties is not None:
            self.setConnectionProperties(connection_properties)

    def setConnectionProperties(self, props):
        if type(props) is not ConnectionProperties:
            raise TypeError("Client.setConnectionProperties: Expected ConnectionProperties object")
        self.prop = props
        if self.prop.extra_headers is not None:
            self.default_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
                }
            self.default_headers.update(self.prop.extra_headers)

    def head(self, url, headers={}, **params):
        url += self.urlencode(params)
        return self.request('HEAD', url, None, headers)

    def get(self, url, headers={}, **params):
        url += self.urlencode(params)
        return self.request('GET', url, None, headers)

    def post(self, url, body=None, headers={}, **params):
        url += self.urlencode(params)
        return self.request('POST', url, json.dumps(body), headers)

    def put(self, url, body=None, headers={}, **params):
        url += self.urlencode(params)
        return self.request('PUT', url, json.dumps(body), headers)

    def delete(self, url, headers={}, **params):
        url += self.urlencode(params)
        return self.request('DELETE', url, None, headers)

    def patch(self, url, body=None, headers={}, **params):
        url += self.urlencode(params)
        return self.request(self.PATCH, url, json.dumps(body), headers)

    def request(self, method, url, body, headers):
        conn = self.get_connection()
        if self.id:
            use_url = '{0}.json'.format(url.replace("id",str(self.id)))
        else:
            use_url = '{0}.json'.format(url)
        print use_url
        conn.request(method, use_url, body, self.default_headers)
        response = conn.getresponse()
        status = response.status
        content = Content(response)
        self.headers = response.getheaders()
        conn.close()
        return status, content.processBody()

    def urlencode(self, params):
        if 'id' in params:
            self.id = params['id']
            del(params['id'])

        if not params:
            return ''
        return '?' + urllib.parse.urlencode(params)


    def get_connection(self):
        print self.prop.api_url
        conn = http.client.HTTPSConnection(self.prop.api_url)
        return conn

class Content(object):
    '''
    Decode a response from the server, respecting the Content-Type field
    '''
    def __init__(self, response):
        self.response = response
        self.body = response.read()
        (self.mediatype, self.encoding) = self.get_ctype()

    def get_ctype(self):
        '''Split the content-type field into mediatype and charset'''
        ctype = self.response.getheader('Content-Type')

        start = 0
        end = 0
        try:
            end = ctype.index(';')
            mediatype = ctype[:end]
        except:
            mediatype = 'x-application/unknown'

        try:
            start = 8 + ctype.index('charset=', end)
            end = ctype.index(';', start)
            charset = ctype[start:end].rstrip()
        except:
            charset = 'ISO-8859-1' #TODO

        return (mediatype, charset)

    def decode_body(self):
        '''
        Decode (and replace) self.body via the charset encoding
        specified in the content-type header
        '''
        self.body = self.body.decode(self.encoding)


    def processBody(self):
        '''
        Retrieve the body of the response, encoding it into a usuable
        form based on the media-type (mime-type)
        '''
        handlerName = self.mangled_mtype()
        handler = getattr(self, handlerName, self.x_application_unknown)
        return handler()


    def mangled_mtype(self):
        '''
        Mangle the media type into a suitable function name
        '''
        return self.mediatype.replace('-','_').replace('/','_')


    ## media-type handlers

    def x_application_unknown(self):
        '''Handler for unknown media-types'''
        return self.body

    def application_json(self):
        '''Handler for application/json media-type'''
        self.decode_body()

        try:
            pybody = json.loads(self.body)
        except ValueError:
            pybody = self.body

        return pybody


class ConnectionProperties(object):
    __slots__ = ['api_url', 'secure_http', 'extra_headers']

    def __init__(self, **props):
        for key in self.__slots__:
            setattr(self, key, None)

        for key, val in props.items():
            if key not in ConnectionProperties.__slots__:
                raise TypeError("Invalid connection property: " + str(key))
            else:
                setattr(self, key, val)
