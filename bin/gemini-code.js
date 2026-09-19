#!/usr/bin/env node

const { spawn, execSync } = require('child_process');
const path = require('path');

const pythonCommands = process.platform === 'win32'
  ? ['python', 'py', 'python3']
  : ['python3', 'python'];

function findPython() {
  for (const cmd of pythonCommands) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      return cmd;
    } catch (e) {
      // continue search
    }
  }
  return null;
}

function ensureDependencies(pythonCmd, projectRoot) {
  try {
    execSync(`${pythonCmd} -c "import rich, httpx, prompt_toolkit"`, { stdio: 'ignore' });
    return true;
  } catch (e) {
    console.log('\x1b[36m[Gemini Code] Первый запуск: устанавливаем необходимые библиотеки...\x1b[0m');
    try {
      const reqPath = path.join(projectRoot, 'requirements.txt');
      execSync(`${pythonCmd} -m pip install -r "${reqPath}"`, { stdio: 'inherit' });
      return true;
    } catch (err) {
      console.warn('\x1b[33m[Предупреждение] Не удалось автоматически выполнить pip install. Если возникнет ошибка импорта, выполните: pip install -r requirements.txt\x1b[0m');
      return false;
    }
  }
}

function run() {
  const pythonCmd = findPython();
  if (!pythonCmd) {
    console.error('\x1b[31m[ERROR] Для работы Gemini Code требуется установленный Python 3.8+.\x1b[0m');
    console.error('Скачайте и установите Python: https://www.python.org/downloads/ (обязательно отметьте галочку "Add python.exe to PATH")');
    process.exit(1);
  }

  const projectRoot = path.resolve(__dirname, '..');
  ensureDependencies(pythonCmd, projectRoot);

  const child = spawn(pythonCmd, ['-m', 'gemini_code.cli', ...process.argv.slice(2)], {
    cwd: process.cwd(),
    stdio: 'inherit',
    env: {
      ...process.env,
      PYTHONPATH: projectRoot + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : '')
    }
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}

run();