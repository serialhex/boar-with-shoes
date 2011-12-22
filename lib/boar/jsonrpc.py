#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "2008-08-31-beta"
__author__   = "Roland Koebler <rk(at)simple-is-better.org>"
__license__  = """Copyright (c) 2007-2008 by Roland Koebler (rk(at)simple-is-better.org)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

#=========================================
#import

import sys
import struct

#=========================================
# errors

#----------------------
# error-codes + exceptions

#JSON-RPC 2.0 error-codes
PARSE_ERROR           = -32700
INVALID_REQUEST       = -32600
METHOD_NOT_FOUND      = -32601
INVALID_METHOD_PARAMS = -32602  #invalid number/type of parameters
INTERNAL_ERROR        = -32603  #"all other errors"

#additional error-codes
PROCEDURE_EXCEPTION    = -32000
AUTHENTIFICATION_ERROR = -32001
PERMISSION_DENIED      = -32002
INVALID_PARAM_VALUES   = -32003

#human-readable messages
ERROR_MESSAGE = {
    PARSE_ERROR           : "Parse error.",
    INVALID_REQUEST       : "Invalid Request.",
    METHOD_NOT_FOUND      : "Method not found.",
    INVALID_METHOD_PARAMS : "Invalid parameters.",
    INTERNAL_ERROR        : "Internal error.",

    PROCEDURE_EXCEPTION   : "Procedure exception.",
    AUTHENTIFICATION_ERROR : "Authentification error.",
    PERMISSION_DENIED   : "Permission denied.",
    INVALID_PARAM_VALUES: "Invalid parameter values."
    }
 
#----------------------
# exceptions

class RPCError(Exception):
    """Base class for rpc-errors."""

class RPCFault(RPCError):
    """RPC error/fault package received.
    
    This exception can also be used as a class, to generate a
    RPC-error/fault message.

    :Variables:
        - error_code:   the RPC error-code
        - error_string: description of the error
        - error_data:   optional additional information
                        (must be json-serializable)
    :TODO: improve __str__
    """
    def __init__(self, error_code, error_message, error_data=None):
        RPCError.__init__(self)
        self.error_code   = error_code
        self.error_message = error_message
        self.error_data   = error_data
    def __str__(self):
        return repr(self)
    def __repr__(self):
        return( "<RPCFault %s: %s (%s)>" % (self.error_code, repr(self.error_message), repr(self.error_data)) )

class RPCParseError(RPCFault):
    """Broken rpc-package. (PARSE_ERROR)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, PARSE_ERROR, ERROR_MESSAGE[PARSE_ERROR], error_data)

class RPCInvalidRPC(RPCFault):
    """Invalid rpc-package. (INVALID_REQUEST)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, INVALID_REQUEST, ERROR_MESSAGE[INVALID_REQUEST], error_data)

class RPCMethodNotFound(RPCFault):
    """Method not found. (METHOD_NOT_FOUND)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, METHOD_NOT_FOUND, ERROR_MESSAGE[METHOD_NOT_FOUND], error_data)

class RPCInvalidMethodParams(RPCFault):
    """Invalid method-parameters. (INVALID_METHOD_PARAMS)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, INVALID_METHOD_PARAMS, ERROR_MESSAGE[INVALID_METHOD_PARAMS], error_data)

class RPCInternalError(RPCFault):
    """Internal error. (INTERNAL_ERROR)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR], error_data)

class RPCProcedureException(RPCFault):
    """Procedure exception. (PROCEDURE_EXCEPTION)"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, PROCEDURE_EXCEPTION, ERROR_MESSAGE[PROCEDURE_EXCEPTION], error_data)
class RPCAuthentificationError(RPCFault):
    """AUTHENTIFICATION_ERROR"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, AUTHENTIFICATION_ERROR, ERROR_MESSAGE[AUTHENTIFICATION_ERROR], error_data)
class RPCPermissionDenied(RPCFault):
    """PERMISSION_DENIED"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, PERMISSION_DENIED, ERROR_MESSAGE[PERMISSION_DENIED], error_data)
class RPCInvalidParamValues(RPCFault):
    """INVALID_PARAM_VALUES"""
    def __init__(self, error_data=None):
        RPCFault.__init__(self, INVALID_PARAM_VALUES, ERROR_MESSAGE[INVALID_PARAM_VALUES], error_data)


#=========================================
# data structure / serializer

if sys.version_info >= (2, 6):
    import json as simplejson
else:
    import simplejson

#----------------------
#
def dictkeyclean(d):
    """Convert all keys of the dict 'd' to (ascii-)strings.

    :Raises: UnicodeEncodeError
    """
    new_d = {}
    for (k, v) in d.iteritems():
        new_d[str(k)] = v
    return new_d

#----------------------
# JSON-RPC 1.0

class DataSource:
    def bytes_left(self):
        """Return the number of bytes that remains to be read from
        this data source."""
        raise NotImplementedError()
    
    def read(self, n):
        """Reads and returns a number of bytes. May return fewer bytes
        than specified if there are no more bytes to read."""
        raise NotImplementedError()

class SocketDataSource(DataSource):
    def __init__(self, socket, data_size):
        self.socket = socket
        self.remaining = data_size
        if self.remaining == 0:
            self.socket.close()

    def bytes_left(self):
        return self.remaining

    def read(self, n):
        if self.remaining == 0:
            return ""
        bytes_to_read = min(n, self.remaining)
        data = RecvNBytes(self.socket, bytes_to_read)
        self.remaining -= bytes_to_read
        assert len(data) == bytes_to_read
        assert len(data) <= n
        assert self.remaining >= 0
        if self.remaining == 0:
            self.socket.close()
        return data

class FileDataSource(DataSource):
    def __init__(self, fo, data_size):
        self.fo = fo
        self.remaining = data_size
        if self.remaining == 0:
            self.fo.close()

    def bytes_left(self):
        return self.remaining

    def read(self, n = None):
        if n == None:
            n = self.remaining
        if self.remaining == 0:
            return ""
        bytes_to_read = min(n, self.remaining)
        data = self.fo.read(bytes_to_read)
        self.remaining -= bytes_to_read
        assert len(data) == bytes_to_read
        assert len(data) <= n
        assert self.remaining >= 0
        if self.remaining == 0:
            self.fo.close()
        return data

def RecvNBytes(socket, n, timeout = None):
    data_parts = []
    readsize = 0
    while readsize < n:
        ready_list = select.select((socket,), (), (), timeout)[0]
        if not ready_list:
            raise Exception("Communication timeout")
        d = socket.recv( min(4096, n - readsize ))
        if len(d) == 0:
            raise Exception("Unexpected end of stream")
        data_parts.append(d)
        readsize += len(d)
    assert readsize == n, "Protocol error. Expected %s bytes, got %s" % (n, readsize)
    data = "".join(data_parts)
    return data    

#----------------------
# JSON-RPC 2.0

class JsonRpc20:
    """JSON-RPC V2.0 data-structure / serializer

    :SeeAlso:   JSON-RPC 2.0 specification
    :TODO:      catch simpeljson.dumps not-serializable-exceptions
    """
    def __init__(self, dumps=simplejson.dumps, loads=simplejson.loads):
        """init: set serializer to use

        :Parameters:
            - dumps: json-encoder-function
            - loads: json-decoder-function
        :Note: The dumps_* functions of this class already directly create
               the invariant parts of the resulting json-object themselves,
               without using the given json-encoder-function.
        """
        self.dumps = simplejson.dumps
        self.loads = simplejson.loads


    def dumps_request( self, method, params=(), id=0 ):
        """serialize JSON-RPC-Request

        :Parameters:
            - method: the method-name (str/unicode)
            - params: the parameters (list/tuple/dict)
            - id:     the id (should not be None)
        :Returns:   | {"jsonrpc": "2.0", "method": "...", "params": ..., "id": ...}
                    | "jsonrpc", "method", "params" and "id" are always in this order.
                    | "params" is omitted if empty
        :Raises:    TypeError if method/params is of wrong type or 
                    not JSON-serializable
        """
        if not isinstance(method, (str, unicode)):
            raise TypeError('"method" must be a string (or unicode string).')
        if not isinstance(params, (tuple, list, dict)):
            raise TypeError("params must be a tuple/list/dict or None.")

        if params:
            return '{"jsonrpc": "2.0", "method": %s, "params": %s, "id": %s}' % \
                    (self.dumps(method), self.dumps(params), self.dumps(id))
        else:
            return '{"jsonrpc": "2.0", "method": %s, "id": %s}' % \
                    (self.dumps(method), self.dumps(id))

    def dumps_response( self, result, id=None ):
        """serialize a JSON-RPC-Response (without error)

        :Returns:   | {"jsonrpc": "2.0", "result": ..., "id": ...}
                    | "jsonrpc", "result", and "id" are always in this order.
        :Raises:    TypeError if not JSON-serializable
        """
        return '{"jsonrpc": "2.0", "result": %s, "id": %s}' % \
                (self.dumps(result), self.dumps(id))

    def dumps_error( self, error, id=None ):
        """serialize a JSON-RPC-Response-error
      
        :Parameters:
            - error: a RPCFault instance
        :Returns:   | {"jsonrpc": "2.0", "error": {"code": error_code, "message": error_message, "data": error_data}, "id": ...}
                    | "jsonrpc", "result", "error" and "id" are always in this order, data is omitted if None.
        :Raises:    ValueError if error is not a RPCFault instance,
                    TypeError if not JSON-serializable
        """
        if not isinstance(error, RPCFault):
            raise ValueError("""error must be a RPCFault-instance.""")
        if error.error_data is None:
            return '{"jsonrpc": "2.0", "error": {"code":%s, "message": %s}, "id": %s}' % \
                    (self.dumps(error.error_code), self.dumps(error.error_message), self.dumps(id))
        else:
            return '{"jsonrpc": "2.0", "error": {"code":%s, "message": %s, "data": %s}, "id": %s}' % \
                    (self.dumps(error.error_code), self.dumps(error.error_message), self.dumps(error.error_data), self.dumps(id))

    def loads_request( self, string ):
        """de-serialize a JSON-RPC Request/Notification

        :Returns:   | [method_name, params, id] or [method_name, params]
                    | params is a tuple/list or dict (with only str-keys)
                    | if id is missing, this is a Notification
        :Raises:    RPCParseError, RPCInvalidRPC, RPCInvalidMethodParams
        """
        try:
            data = self.loads(string)
        except ValueError, err:
            raise RPCParseError("No valid JSON. (%s)" % str(err))
        if not isinstance(data, dict):  raise RPCInvalidRPC("No valid RPC-package.")
        if "jsonrpc" not in data:       raise RPCInvalidRPC("""Invalid Response, "jsonrpc" missing.""")
        if not isinstance(data["jsonrpc"], (str, unicode)):
            raise RPCInvalidRPC("""Invalid Response, "jsonrpc" must be a string.""")
        if data["jsonrpc"] != "2.0":    raise RPCInvalidRPC("""Invalid jsonrpc version.""")
        if "method" not in data:        raise RPCInvalidRPC("""Invalid Request, "method" is missing.""")
        if not isinstance(data["method"], (str, unicode)):
            raise RPCInvalidRPC("""Invalid Request, "method" must be a string.""")
        if "params" not in data:        data["params"] = ()
        #convert params-keys from unicode to str
        elif isinstance(data["params"], dict):
            try:
                data["params"] = dictkeyclean(data["params"])
            except UnicodeEncodeError:
                raise RPCInvalidMethodParams("Parameter-names must be in ascii.")
        elif not isinstance(data["params"], (list, tuple)):
            raise RPCInvalidRPC("""Invalid Request, "params" must be an array or object.""")
        if not( len(data)==3 or ("id" in data and len(data)==4) ):
            raise RPCInvalidRPC("""Invalid Request, additional fields found.""")

        assert "id" in data, "JsonRPC notifications not supported"
        return data["method"], data["params"], data["id"]

    def loads_response( self, string ):
        """de-serialize a JSON-RPC Response/error

        :Returns: | [result, id] for Responses
        :Raises:  | RPCFault+derivates for error-packages/faults, RPCParseError, RPCInvalidRPC
        """
        try:
            data = self.loads(string)
        except ValueError, err:
            raise RPCParseError("No valid JSON. (%s)" % str(err))
        if not isinstance(data, dict):  raise RPCInvalidRPC("No valid RPC-package.")
        if "jsonrpc" not in data:       raise RPCInvalidRPC("""Invalid Response, "jsonrpc" missing.""")
        if not isinstance(data["jsonrpc"], (str, unicode)):
            raise RPCInvalidRPC("""Invalid Response, "jsonrpc" must be a string.""")
        if data["jsonrpc"] != "2.0":    raise RPCInvalidRPC("""Invalid jsonrpc version.""")
        if "id" not in data:            raise RPCInvalidRPC("""Invalid Response, "id" missing.""")
        if "result" not in data:        data["result"] = None
        if "error"  not in data:        data["error"]  = None
        if len(data) != 4:              raise RPCInvalidRPC("""Invalid Response, additional or missing fields.""")

        #error
        if data["error"] is not None:
            if data["result"] is not None:
                raise RPCInvalidRPC("""Invalid Response, only "result" OR "error" allowed.""")
            if not isinstance(data["error"], dict): raise RPCInvalidRPC("Invalid Response, invalid error-object.")
            if "code" not in data["error"]  or  "message" not in data["error"]:
                raise RPCInvalidRPC("Invalid Response, invalid error-object.")
            if "data" not in data["error"]:  data["error"]["data"] = None
            if len(data["error"]) != 3:
                raise RPCInvalidRPC("Invalid Response, invalid error-object.")

            error_data = data["error"]["data"]
            if   data["error"]["code"] == PARSE_ERROR:
                raise RPCParseError(error_data)
            elif data["error"]["code"] == INVALID_REQUEST:
                raise RPCInvalidRPC(error_data)
            elif data["error"]["code"] == METHOD_NOT_FOUND:
                raise RPCMethodNotFound(error_data)
            elif data["error"]["code"] == INVALID_METHOD_PARAMS:
                raise RPCInvalidMethodParams(error_data)
            elif data["error"]["code"] == INTERNAL_ERROR:
                raise RPCInternalError(error_data)
            elif data["error"]["code"] == PROCEDURE_EXCEPTION:
                raise RPCProcedureException(error_data)
            elif data["error"]["code"] == AUTHENTIFICATION_ERROR:
                raise RPCAuthentificationError(error_data)
            elif data["error"]["code"] == PERMISSION_DENIED:
                raise RPCPermissionDenied(error_data)
            elif data["error"]["code"] == INVALID_PARAM_VALUES:
                raise RPCInvalidParamValues(error_data)
            else:
                raise RPCFault(data["error"]["code"], data["error"]["message"], error_data)
        #result
        else:
            return data["result"], data["id"]

jsonrpc20 = JsonRpc20()

#=========================================
# transports

#----------------------
# transport-logging

import codecs
import time

t0 = time.time()

def log_dummy( message ):
    """dummy-logger: do nothing"""
    #print round(time.time() - t0, 2), message
    pass

def log_stdout( message ):
    """print message to STDOUT"""
    print message

def log_file( filename ):
    """return a logfunc which logs to a file (in utf-8)"""
    def logfile( message ):
        f = codecs.open( filename, 'a', encoding='utf-8' )
        f.write( message+"\n" )
        f.close()
    return logfile

def log_filedate( filename ):
    """return a logfunc which logs date+message to a file (in utf-8)"""
    def logfile( message ):
        f = codecs.open( filename, 'a', encoding='utf-8' )
        f.write( time.strftime("%Y-%m-%d %H:%M:%S ")+message+"\n" )
        f.close()
    return logfile

#----------------------

HEADER_SIZE=17
HEADER_MAGIC=0x12345678
HEADER_VERSION=1
"""
The header has 
"""
def pack_header(payload_size, binary_payload_size = None):
    has_binary_payload = True
    if binary_payload_size == None:
        has_binary_payload = False
        binary_payload_size = 0
    header_str = struct.pack("!III?I", HEADER_MAGIC, HEADER_VERSION, payload_size,\
                                 has_binary_payload, binary_payload_size)
    assert len(header_str) == HEADER_SIZE
    return header_str

def unpack_header(header_str):
    assert len(header_str) == HEADER_SIZE
    magic, version, payload_size, has_binary_payload, binary_payload_size = \
        struct.unpack("!III?I", header_str)
    assert magic == HEADER_MAGIC, header_str
    if not has_binary_payload:
        assert binary_payload_size == 0
        binary_payload_size = None
    return payload_size, binary_payload_size

import socket, select
class TransportTcpIp:
    """Transport via socket.
   
    :SeeAlso:   python-module socket
    :TODO:
        - documentation
        - improve this (e.g. make sure that connections are closed, socket-files are deleted etc.)
        - exception-handling? (socket.error)
    """
    def __init__( self, addr = None, limit=4096, sock_type=socket.AF_INET, sock_prot=socket.SOCK_STREAM, timeout=1.0, logfunc=log_dummy ):
        """
        :Parameters:
            - addr: socket-address
            - timeout: timeout in seconds
            - logfunc: function for logging, logfunc(message)
        :Raises: socket.timeout after timeout
        """
        self.limit  = limit
        self.addr   = addr
        self.s_type = sock_type
        self.s_prot = sock_prot
        self.s      = None
        self.timeout = timeout
        self.log    = logfunc

    def connect( self ):
        self.close()
        self.log( "connect to %s" % repr(self.addr) )
        self.s = socket.socket( self.s_type, self.s_prot )
        self.s.settimeout( self.timeout )
        self.s.connect( self.addr )

    def close( self ):
        if self.s is not None:
            self.log( "close %s" % repr(self.addr) )
            self.s.close()
            self.s = None

    def __repr__(self):
        return "<TransportSocket, %s>" % repr(self.addr)
    
    def send( self, string ):
        if self.s is None:
            self.connect()
        header = pack_header(len(string))
        self.s.sendall( header )
        self.s.sendall( string )
        self.log( "TransportSocket.Send() --> "+repr(string) )
        
    def recv( self ):
        if self.s is None:
            self.connect()
        header = RecvNBytes(self.s, HEADER_SIZE)
        datasize, binary_data_size = unpack_header(header)
        data = RecvNBytes(self.s, datasize, 5.0)
        self.log( "TransportSocket.Recv() --> "+repr(data) )
        if binary_data_size != None:            
            return data, SocketDataSource(self.s, binary_data_size)
        else:
            return data, None

    def sendrecv( self, string ):
        """send data + receive data + close"""
        self.close()
        data_source = None
        try:
            self.log("SendRecv id = " + str(id(self)))
            self.send( string )
            self.log("SendRecv Waiting for reply")
            reply, data_source = self.recv()
            self.log("SendRecv Got a reply")
            return reply, data_source
        finally: 
            if data_source == None:
                self.close()

    def init_server(self):
        if self.s:
            return
        self.close()
        self.s = socket.socket( self.s_type, self.s_prot )
        self.log( "Server id %s listens at %s" % (id(self),self.addr) )
        self.s.bind( self.addr )
        self.s.listen(1)

    def serve(self, handler, n=None):
        """open socket, wait for incoming connections and handle them.
        
        :Parameters:
            - n: serve n requests, None=forever
        """
        try:
            self.init_server()
            n_current = 0
            while 1:
                if n is not None  and  n_current >= n:
                    break
                conn, addr = self.s.accept()
                self.log( "TransportSocket.Serve(): %s connected" % repr(addr) )
                header = RecvNBytes(conn, HEADER_SIZE)
                self.log( "TransportSocket.Serve(): got an header")
                datasize, binary_data_size = unpack_header(header)
                assert binary_data_size == None, "Not implemented yet. Was: " + str(binary_data_size)
                data = RecvNBytes(conn, datasize, 5.0)
                self.log( "TransportSocket.Serve(): Got a message: %s --> %s" % (repr(addr), repr(data)) )
                result = handler(data)
                self.log( "TransportSocket.Serve(): Message was handled ok" )
                assert result != None
                self.log( "TransportSocket.Serve(): Responding to %s <-- %s" % (repr(addr), repr(result)) )  
                if isinstance(result, DataSource):
                    dummy_result = jsonrpc20.dumps_response(None)
                    header = pack_header(len(dummy_result), result.bytes_left())
                    conn.sendall( header )
                    conn.sendall( dummy_result )
                    while result.bytes_left() > 0:
                        conn.sendall(result.read(2**14))
                else:
                    header = pack_header(len(result))
                    conn.sendall( header )
                    conn.sendall( result )
                self.log( "TransportSocket.Serve(): Response sent" )
                self.log( "TransportSocket.Serve(): %s close" % repr(addr) )
                conn.close()
                n_current += 1
        finally:
            self.close()


#=========================================
# client side: server proxy

class ServerProxy:
    """RPC-client: server proxy

    A logical connection to a RPC server.

    It works with different data/serializers and different transports.

    Notifications and id-handling/multicall are not yet implemented.

    :Example:
        see module-docstring

    :TODO: verbose/logging?
    """
    def __init__( self, data_serializer, transport ):
        """
        :Parameters:
            - data_serializer: a data_structure+serializer-instance
            - transport: a Transport instance
        """
        #TODO: check parameters
        self.__data_serializer = data_serializer
        self.__transport = transport

    def __str__(self):
        return repr(self)
    def __repr__(self):
        return "<ServerProxy for %s, with serializer %s>" % (self.__transport, self.__data_serializer)

    def __req( self, methodname, args=None, kwargs=None, id=0 ):
        # JSON-RPC 2.0: only args OR kwargs allowed!
        if len(args) > 0 and len(kwargs) > 0:
            raise ValueError("Only positional or named parameters are allowed!")
        if len(kwargs) == 0:
            req_str  = self.__data_serializer.dumps_request( methodname, args, id )
        else:
            req_str  = self.__data_serializer.dumps_request( methodname, kwargs, id )

        resp_str, data_source = self.__transport.sendrecv( req_str )
        if data_source:
            return data_source
        resp = self.__data_serializer.loads_response( resp_str )
        return resp[0]

    def __getattr__(self, name):
        # magic method dispatcher
        #  note: to call a remote object with an non-standard name, use
        #  result getattr(my_server_proxy, "strange-python-name")(args)
        return _method(self.__req, name)

# request dispatcher
class _method:
    """some "magic" to bind an RPC method to an RPC server.

    Supports "nested" methods (e.g. examples.getStateName).

    :Raises: AttributeError for method-names/attributes beginning with '_'.
    """
    def __init__(self, req, name):
        if name[0] == "_":  #prevent rpc-calls for proxy._*-functions
            raise AttributeError("invalid attribute '%s'" % name)
        self.__req  = req
        self.__name = name
    def __getattr__(self, name):
        if name[0] == "_":  #prevent rpc-calls for proxy._*-functions
            raise AttributeError("invalid attribute '%s'" % name)
        return _method(self.__req, "%s.%s" % (self.__name, name))
    def __call__(self, *args, **kwargs):
        return self.__req(self.__name, args, kwargs)

#=========================================
# server side: Server

class Server:
    """RPC-server.

    It works with different data/serializers and 
    with different transports.

    :Example:
        see module-docstring

    :TODO:
        - mixed JSON-RPC 1.0/2.0 server?
        - logging/loglevels?
    """
    def __init__( self, data_serializer, transport, logfile=None ):
        """
        :Parameters:
            - data_serializer: a data_structure+serializer-instance
            - transport: a Transport instance
            - logfile: file to log ("unexpected") errors to
        """
        #TODO: check parameters
        self.__data_serializer = data_serializer
        self.__transport = transport
        self.__transport.init_server()
        self.logfile = logfile
        if self.logfile is not None:    #create logfile (or raise exception)
            f = codecs.open( self.logfile, 'a', encoding='utf-8' )
            f.close()

        self.funcs = {}

    def __repr__(self):
        return "<Server for %s, with serializer %s>" % (self.__transport, self.__data_serializer)

    def log(self, message):
        """write a message to the logfile (in utf-8)"""
        if self.logfile is not None:
            f = codecs.open( self.logfile, 'a', encoding='utf-8' )
            f.write( time.strftime("%Y-%m-%d %H:%M:%S ")+message+"\n" )
            f.close()

    def register_instance(self, myinst, name=None):
        """Add all functions of a class-instance to the RPC-services.
        
        All entries of the instance which do not begin with '_' are added.

        :Parameters:
            - myinst: class-instance containing the functions
            - name:   | hierarchical prefix.
                      | If omitted, the functions are added directly.
                      | If given, the functions are added as "name.function".
        :TODO:
            - only add functions and omit attributes?
            - improve hierarchy?
        """
        for e in dir(myinst):
            if e[0][0] != "_":
                if name is None:
                    self.register_function( getattr(myinst, e) )
                else:
                    self.register_function( getattr(myinst, e), name="%s.%s" % (name, e) )
    def register_function(self, function, name=None):
        """Add a function to the RPC-services.
        
        :Parameters:
            - function: function to add
            - name:     RPC-name for the function. If omitted/None, the original
                        name of the function is used.
        """
        if name is None:
            self.funcs[function.__name__] = function
        else:
            self.funcs[name] = function
    
    def handle(self, rpcstr):
        """Handle a RPC-Request.

        :Parameters:
            - rpcstr: the received rpc-string
        :Returns: the data to send back or None if nothing should be sent back
        :Raises:  RPCFault (and maybe others)
        """
        #TODO: id
        try:
            req = self.__data_serializer.loads_request( rpcstr )
            if len(req) == 2:
                raise RPCFault("JsonRPC notifications not supported")
            method, params, id = req
        except RPCFault, err:
            return self.__data_serializer.dumps_error( err, id=None )
        except Exception, err:
            self.log( "%d (%s): %s" % (INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR], str(err)) )
            return self.__data_serializer.dumps_error( RPCFault(INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR]), id=None )

        if method not in self.funcs:
            return self.__data_serializer.dumps_error( RPCFault(METHOD_NOT_FOUND, ERROR_MESSAGE[METHOD_NOT_FOUND]), id )

        try:
            if isinstance(params, dict):
                result = self.funcs[method]( **params )
            else:
                result = self.funcs[method]( *params )
            if isinstance(result, DataSource):
                return result

        except RPCFault, err:
            return self.__data_serializer.dumps_error( err, id=None )
        except Exception, err:
            print( "%d (%s): %s" % (INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR], str(err)) )
            return self.__data_serializer.dumps_error( RPCFault(INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR]), id )

        try:
            return self.__data_serializer.dumps_response( result, id )
        except Exception, err:
            self.log( "%d (%s): %s" % (INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR], str(err)) )
            return self.__data_serializer.dumps_error( RPCFault(INTERNAL_ERROR, ERROR_MESSAGE[INTERNAL_ERROR]), id )

    def serve(self, n=None):
        """serve (forever or for n communicaions).
        
        :See: Transport
        """
        self.__transport.serve( self.handle, n )

#=========================================

