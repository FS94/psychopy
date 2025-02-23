#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for hardware device interfaces.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'BaseDevice'
]


class BaseResponse:
    """
    Base class for device responses.
    """
    # list of fields known to be a part of this response type
    fields = ["t", "value"]

    def __init__(self, t, value):
        self.t = t
        self.value = value

    def __repr__(self):
        # make key=val strings
        attrs = []
        for key in self.fields:
            attrs.append(f"{key}={getattr(self, key)}")
        attrs = ", ".join(attrs)
        # construct
        return f"<{type(self).__name__}: {attrs}>"

    def getJSON(self):
        import json
        # construct message as dict
        message = {
            'type': "hardware_response",
            'class': type(self).__name__,
            'data': {}
        }
        # add all fields to "data"
        for key in self.fields:
            message['data'][key] = getattr(self, key)

        return json.dumps(message)


class BaseDevice:
    """
    Base class for device interfaces, includes support for DeviceManager and adding listeners.
    """
    def __init_subclass__(cls, aliases=None):
        from psychopy.hardware.manager import DeviceManager
        import inspect
        # handle no aliases
        if aliases is None:
            aliases = []
        # if given a class, get its class string
        mro = inspect.getmodule(cls).__name__ + "." + cls.__name__
        # register aliases
        for alias in aliases:
            DeviceManager.registerClassAlias(alias, mro)
        # store class string
        DeviceManager.deviceClasses.append(mro)

        return cls

    @staticmethod
    def getAvailableDevices():
        """
        Get all available devices of this type.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `getAvailableDevices`"
        )


class BaseResponseDevice(BaseDevice):

    responseClass = BaseResponse

    def __init__(self):
        # list to store listeners in
        self.listeners = []
        # list to store responses in
        self.responses = []

    def dispatchMessages(self):
        """
        Method to dispatch messages from the device to any nodes or listeners attached.
        """
        pass

    def parseMessage(self, message):
        raise NotImplementedError(
            "All subclasses of BaseDevice must implement the method `parseMessage`"
        )

    def receiveMessage(self, message):
        """
        Method called when a parsed message is received. Includes code to send to any listeners and store the response.

        Parameters
        ----------
        message
            Parsed message, should be an instance of this Device's `responseClass`

        Returns
        -------
        bool
            True if completed successfully
        """
        assert isinstance(message, self.responseClass), (
            "{ownType}.receiveMessage() can only receive messages of type {targetType}, instead received "
            "{msgType}. Try parsing the message first using {ownType}.parseMessage()"
        ).format(ownType=type(self).__name__, targetType=self.responseClass.__name__, msgType=type(message).__name__)
        # add message to responses
        self.responses.append(message)
        # relay message to listener
        for listener in self.listeners:
            listener.receiveMessage(message)

        return True

    def makeResponse(self, *args, **kwargs):
        """
        Programatically make a response on this device. The device won't necessarily physically register the response,
        but it will be stored in this object same as an actual response.

        Parameters
        ----------
        Function takes the same inputs as the response class for this device. For example, in KeyboardDevice, inputs
        are code, tDown and name.

        Returns
        -------
        BaseResponse
            The response object created
        """
        # create response
        resp = self.responseClass(*args, **kwargs)
        # receive response
        self.receiveMessage(resp)

        return resp

    def clearResponses(self):
        """
        Clear any responses stored on this Device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # try to dispatch messages
        try:
            self.dispatchMessages()
        except:
            pass
        # clear resp list
        self.responses = []

        return True

    def getListenerNames(self):
        return [type(lsnr).__name__ for lsnr in self.listeners]

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch messages.
        """
        from . import listener as lsnr
        # make listener if needed
        if not isinstance(listener, lsnr.BaseListener):
            # if given a string rather than an object handle, make an object of correct type
            if listener == "liaison":
                from psychopy.hardware import DeviceManager
                if DeviceManager.liaison is None:
                    raise AttributeError(
                        "Cannot create a `liaison` listener as no liaison server is connected to DeviceManager."
                    )
                listener = lsnr.LiaisonListener(DeviceManager.liaison)
            if listener == "print":
                listener = lsnr.PrintListener()
            if listener == "log":
                listener = lsnr.LoggingListener()
        # add listener handle
        self.listeners.append(listener)
        # start loop if requested
        if startLoop:
            listener.startLoop(self)

        return listener

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # remove listeners from loop
        for listener in self.listeners:
            listener.loop.removeDevice(listener)
        # clear list
        self.listeners = []

        return True

if __name__ == "__main__":
    pass
