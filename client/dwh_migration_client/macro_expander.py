# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Macro handling classes """

import re
import logging
from typing import Callable, Dict, List, Optional, Tuple, Set
from fnmatch import fnmatch



class MacroExpander:

    # macro name -> replacement
    mapping: Optional[Dict[str, str]]
    # file name -> [replacement -> original(s)]
    reverse: Dict[str, Dict[str, Tuple[int, Set[str]]]]
    # function for generating values when a macro is missing from 'mapping'
    generator: Optional[Callable[[str, str], str]]
    # function for custom un-expanding of macros
    un_generator: Optional[Callable[[str, str, str], str]]
    # file name -> unmapped macros
    unmapped: Dict[str, Set[str]]

    def __init__(
        self,
        pattern: str,
        mapping: Optional[Dict[str, str]] = None,
        generator: Optional[Callable[[str, str], str]] = None,
        un_generator: Optional[Callable[[str, str, str], str]] = None,
    ) -> None:
        """Does some stuff"""
        self.pattern = re.compile(pattern, re.I)
        self.generator = generator
        self.un_generator = un_generator
        self.mapping = mapping
        self.reverse = {}
        self.unmapped = {}

    def _sanity_check(self, file_name: str) -> None:
        for replacement, originals in self.reverse[file_name].items():
            if len(originals[1]) > 1:
                logging.warn(
                    "The value '%s' was expanded from "
                    + "the following macros: %s. Un-expansion will not "
                    + "be accurate.", replacement, originals[1]
                )

    def _substitution(self, file_name: str, match) -> str:
        macro_name = match.group(1)
        full_match = match.group(0)
        generated = None
        if self.mapping and macro_name in self.mapping:
            generated = self.mapping[macro_name]
        elif self.generator:
            if file_name in self.unmapped:
                self.unmapped[file_name].union(macro_name)
            else:
                self.unmapped[file_name] = {macro_name}
            generated = self.generator(file_name, macro_name)
        else:
            logging.warn(
                "Could not expand '%s' as it is not "
                + "present in the mapping and no generator function was "
                + "provided", full_match
            )
            generated = full_match
        if not file_name in self.reverse:
            self.reverse[file_name] = {}
        reverse_for_file = self.reverse[file_name]
        if generated in reverse_for_file:
            reverse_for_file[generated] = (
                reverse_for_file[generated][0] + 1,
                reverse_for_file[generated][1].union({full_match}),
            )
        else:
            reverse_for_file[generated] = (1, {full_match})
        return generated

    def expand(self, file_name: str, text: str) -> str:
        return self.pattern.sub(
            lambda match: self._substitution(file_name, match), text
        )

    def un_expand(self, file_name: str, text: str) -> str:
        if not file_name in self.reverse:
            return text
        self._sanity_check(file_name)
        for replacement, original in self.reverse[file_name].items():
            result = None
            original_text = original[1].pop()
            if self.un_generator:
                result = re.subn(
                    re.escape(replacement),
                    self.un_generator(file_name, replacement, original_text),
                    text,
                    flags=re.I
                )
            else:
                result = re.subn(re.escape(replacement), original_text, text)
            if False: # Generates too many false positives
                if result[1] > original[0]:
                    logging.warning(
                        "The string '%s' was un-expanded "
                        + "to '%s' %s times, but was only the "
                        + "result of an expansion %s time(s).",
                        replacement, original_text, result[1], original[0]
                    )
            text = result[0]
        return text


class MacroExpanderRouter:
    all_macros: Dict[str, MacroExpander]

    def __init__(self, all_macros: Dict[str, MacroExpander]) -> None:
        self.all_macros = all_macros

    def choose_expander(self, file_name: str) -> Optional[MacroExpander]:
        chosen_expander = None
        chosen_pattern = None
        matches = []
        for pattern, expander in self.all_macros.items():
            if fnmatch(file_name, pattern):
                matches.append(file_name)
                chosen_expander = expander
                chosen_pattern = pattern
        if len(matches) == 0:
            return None
        if len(matches) > 1:
            loggin.warn(
                "File name %s matches multiple patterns. Arbitrarily choosing '%s'.",
                file_name, chosen_pattern
            )
        return chosen_expander

    def expand(self, file_name: str, text: str) -> str:
        expander = self.choose_expander(file_name)
        if expander:
            return expander.expand(file_name, text)
        return text

    def un_expand(self, file_name: str, text: str) -> str:
        expander = self.choose_expander(file_name)
        if expander:
            return expander.un_expand(file_name, text)
        return text
