#
# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id$
#


from distutils.core import setup, Extension

long_description = """Python language control flow parser.
Written as a part of the Codimension project, this parser
aims at pulling all the necessery data to build a control
flow diagram."""

version = 'trunk'

setup( name = 'cdmpycfparser',
       description = 'Codimension Python Control Flow Parser',
       long_description = long_description,
       version = version,
       author = 'Sergey Satskiy',
       author_email = 'sergey.satskiy@gmail.com',
       url = 'http://satsky.spb.ru/codimension/',
       license = 'GPLv3',
       classifiers = [
           'Development Status :: 5 - Production/Stable',
           'Intended Audience :: Developers',
           'License :: OSI Approved :: GNU General Public License (GPL)',
           'Operating System :: POSIX :: Linux',
           'Programming Language :: C',
           'Programming Language :: Python',
           'Topic :: Software Development :: Libraries :: Python Modules'],
       platforms = [ 'any' ],
       py_modules  = [ 'cdmcfparser' ],
       ext_modules = [ Extension( '_cdmpycfparser',
                                  [ 'cdmpycfparser.c',
                                    'lexerutils.c',
                                    'pythoncontrolflowLexer.c',
                                    'pythoncontrolflowParser.c' ],
                                  extra_compile_args = [ '-Wno-unused', '-fomit-frame-pointer',
                                                         '-DCDM_PY_PARSER_VERSION="' + version + '"',
                                                         '-I../thirdparty/libantlr3c-3.2',
                                                         '-I../thirdparty/libantlr3c-3.2/include',
                                                         '-ffast-math' ],
                                  extra_link_args = [ '../thirdparty/libantlr3c-3.2/.libs/libantlr3c.a' ]
                                ) ] )

