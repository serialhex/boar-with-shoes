# -*- coding: utf-8 -*-

# Copyright 2010 Mats Ekberg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class UserError(Exception):
    """This exception is thrown when an error has occured that is not
    caused by a malfunction in boar. For instance, trying to access a
    repository by the wrong path."""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SessionNotFoundError(UserError):
    """This exception is thrown when an attempt has been made to
    access a non-existing session."""
    pass

