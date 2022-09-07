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
"""Doc string."""

import re
from dwh_migration_client.macro_expander import MacroExpander, MacroExpanderRouter

def un_generator(file_name: str, replacement: str, macro_name: str) -> str:
	match = re.match("PARAM_(.+)_PARAM", replacement)
	if match:
		unexpanded = match.group(1)
	else:
		unexpanded = macro_name
	return "{" + unexpanded + "}"

expander = MacroExpander(
	pattern="\\$\\{(\\w+)\\}",
	generator=lambda file_name, macro_name: "PARAM_" + macro_name.lower() + "_PARAM",
	un_generator=un_generator,
)

aurigae_macro_router = MacroExpanderRouter({
    "*.sql": expander,
	"*.bteq": expander
    }
)
