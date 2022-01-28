from fabric import task

@task
def deploy(c, branch='main'):
    print('Start deploying!')
    # stop container
    result = c.run('cd poe-trade-bot && docker-compose down', warn=True)
    print(result.stdout)

    # remove folder
    result = c.run('rm -rf poe-trade-bot', warn=True)
    print('remove old folder...')

    # clone from github
    result = c.run("git clone -b {} --single-branch git@github.com:HowToLose/poe-trade-bot.git".format(branch), warn=True)
    print(result.stdout)

    # clone env file
    result = c.run('cp shared/.poe-trade-bot.env poe-trade-bot/.env', warn=True)
    print('copy env file...')

    # run docker compose
    result = c.run('cd poe-trade-bot && docker-compose up --build --remove-orphans -d', warn=True)
    print(result.stdout)
    print('Done!')
