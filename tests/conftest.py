import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from pr_diff_walk.schemas import RepositoryFiles


@pytest.fixture
def temp_repo_dir():
    with tempfile.TemporaryDirectory(prefix="test_repo_") as td:
        yield Path(td)


@pytest.fixture
def sample_js_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/utils.js": """
export function add(a, b) {
    return a + b;
}

export const PI = 3.14;
""",
        "src/index.js": """
import { add, PI } from './utils.js';
console.log(add(1, 2));
""",
        "src/components/Button.jsx": """
import React from 'react';
import { add } from '../utils.js';

export const Button = () => {
    return <button>{add(1, 2)}</button>;
};
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_ts_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/types.ts": """
export interface User {
    id: number;
    name: string;
}

export type Status = 'active' | 'inactive';
""",
        "src/service.ts": """
import { User, Status } from './types';

export class UserService {
    getUser(): User {
        return { id: 1, name: 'Test' };
    }
}
""",
        "src/app.tsx": """
import React from 'react';
import { UserService } from './service';

export const App = () => {
    const service = new UserService();
    return <div>{service.getUser().name}</div>;
};
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_python_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "utils.py": """
def add(a, b):
    return a + b

PI = 3.14
""",
        "__init__.py": """
from .utils import add, PI
""",
        "src/main.py": """
from utils import add, PI

def main():
    print(add(1, 2))
""",
        "src/models.py": """
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_rust_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/lib.rs": """
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub const PI: f64 = 3.14;
""",
        "src/main.rs": """
use crate::add;

fn main() {
    println!("{}", add(1, 2));
}
""",
        "src/math.rs": """
pub struct Calculator {
    value: i32,
}

impl Calculator {
    pub fn new() -> Self {
        Calculator { value: 0 }
    }
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_go_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "utils.go": """
package main

func Add(a, b int) int {
    return a + b
}

const Pi = 3.14
""",
        "main.go": """
package main

func main() {
    result := Add(1, 2)
    println(result)
}
""",
        "models/user.go": """
package models

type User struct {
    Name string
    Age  int
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_java_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/main/java/Utils.java": """
public class Utils {
    public static int add(int a, int b) {
        return a + b;
    }
    
    public static final double PI = 3.14;
}
""",
        "src/main/java/Main.java": """
public class Main {
    public static void main(String[] args) {
        int result = Utils.add(1, 2);
        System.out.println(result);
    }
}
""",
        "src/main/java/models/User.java": """
package models;

public class User {
    private String name;
    private int age;
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_csharp_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/Utils.cs": """
namespace Utils {
    public class Math {
        public static int Add(int a, int b) => a + b;
    }
}
""",
        "src/Program.cs": """
namespace App {
    class Program {
        static void Main() {
            var result = Utils.Math.Add(1, 2);
        }
    }
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_dart_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "lib/utils.dart": """
int add(int a, int b) => a + b;

const pi = 3.14;
""",
        "lib/main.dart": """
import 'utils.dart';

void main() {
  print(add(1, 2));
}
""",
        "lib/models/user.dart": """
class User {
  String name;
  int age;
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_swift_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "Sources/App/utils.swift": """
func add(_ a: Int, _ b: Int) -> Int {
    return a + b
}

let pi = 3.14
""",
        "Sources/App/main.swift": """
import Foundation

print(add(1, 2))
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_kotlin_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/main/kotlin/Utils.kt": """
fun add(a: Int, b: Int) = a + b

const val pi = 3.14

class Calculator {
    fun calculate() = 42
}
""",
        "src/main/kotlin/Main.kt": """
fun main() {
    println(add(1, 2))
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_c_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/utils.h": """
#ifndef UTILS_H
#define UTILS_H

int add(int a, int b);
#define PI 3.14

#endif
""",
        "src/utils.c": """
#include "utils.h"

int add(int a, int b) {
    return a + b;
}
""",
        "src/main.c": """
#include "utils.h"

int main() {
    return add(1, 2);
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_cpp_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "include/utils.hpp": """
#ifndef UTILS_HPP
#define UTILS_HPP

namespace utils {
    int add(int a, int b) {
        return a + b;
    }
    constexpr double PI = 3.14;
}

#endif
""",
        "src/main.cpp": """
#include "utils.hpp"

int main() {
    return utils::add(1, 2);
}
""",
        "src/math.cpp": """
#include "utils.hpp"

class Math {
public:
    int calculate() { return 42; }
};
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_zig_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/main.zig": """
const std = @import("std");

pub fn add(a: i32, b: i32) i32 {
    return a + b;
}

pub fn main() void {
    _ = add(1, 2);
}
""",
        "src/math.zig": """
pub const PI: f64 = 3.14;

pub fn multiply(a: f64, b: f64) f64 {
    return a * b;
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_php_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/Utils.php": (
            "<?php\n\n"
            "namespace App;\n\n"
            "class Utils {\n"
            "    public static function add($a, $b) {\n"
            "        return $a + $b;\n"
            "    }\n\n"
            "    const PI = 3.14;\n"
            "}\n"
        ),
        "src/main.php": (
            "<?php\n\n"
            "require_once 'Utils.php';\n\n"
            "use App\\Utils;\n\n"
            "$result = Utils::add(1, 2);\n"
        ),
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_html_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "index.html": """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <script src="app.js"></script>
</body>
</html>
""",
        "styles.css": """
body {
    background: white;
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_css_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "styles.css": """
:root {
    --primary: blue;
}

.class-name {
    color: red;
}

#element-id {
    background: green;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
""",
        "components/button.css": """
.btn {
    padding: 10px;
}
""",
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_mixed_files(temp_repo_dir: Path) -> Dict[str, str]:
    files = {
        "src/utils.py": """
def py_add(a, b):
    return a + b
""",
        "src/helper.js": """
export function js_add(a, b) {
    return a + b;
}
""",
        "src/main.ts": """
import { py_add } from './utils.py';
import { js_add } from './helper.js';

export function combined(a, b) {
    return py_add(a, b) + js_add(a, b);
}
""",
        "README.md": "# Mixed Language Project",
        "src/config.json": '{"version": "1.0"}',
    }
    for path, content in files.items():
        full_path = temp_repo_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    return files


@pytest.fixture
def sample_patch():
    return """diff -- src/utils.js [modified]
--- a/src/utils.js
+++ b/src/utils.js
@@ -1,5 +1,7 @@
 export function add(a, b) {
-    return a + b;
+    const result = a + b;
+    console.log('Adding:', result);
+    return result;
 }

 export const PI = 3.14;
"""


@pytest.fixture
def sample_pr_files():
    return [
        {"filename": "src/utils.js", "status": "modified", "patch": "export function add(a, b) {\n+    return a + b;\n}"},
        {"filename": "src/main.py", "status": "added", "patch": "def new_func():\n+    pass"},
        {"filename": "README.md", "status": "modified", "patch": ""},
    ]
