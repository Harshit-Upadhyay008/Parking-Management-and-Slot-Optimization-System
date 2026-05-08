module.exports = {
  apps: [
    {
      name: 'smart-parking',
      script: 'python',
      args: 'manage.py runserver 0.0.0.0:3000',
      cwd: '/home/user/webapp',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      watch: false,
      instances: 1,
      exec_mode: 'fork'
    }
  ]
}
