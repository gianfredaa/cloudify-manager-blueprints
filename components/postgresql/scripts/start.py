#!/usr/bin/env python

import os
import tempfile
from os.path import join, dirname

from cloudify import ctx

ctx.download_resource(
    join('components', 'utils.py'),
    join(dirname(__file__), 'utils.py'))
import utils  # NOQA

PS_SERVICE_NAME = 'postgresql-9.5'
ctx_properties = utils.ctx_factory.get(PS_SERVICE_NAME)


def _start_postgres():
    ctx.logger.info('Starting PostgreSQL Service...')
    utils.systemd.stop(service_name=PS_SERVICE_NAME,
                       append_prefix=False)
    utils.systemd.start(service_name=PS_SERVICE_NAME,
                        append_prefix=False)
    utils.systemd.verify_alive(service_name=PS_SERVICE_NAME,
                               append_prefix=False)


def _create_default_db(db_name, username, password):
    ctx.logger.info('Creating default postgresql database: {0}...'.format(
        db_name))
    ps_config_source = 'components/postgresql/config/create_default_db.sh'
    ps_config_destination = join(tempfile.gettempdir(),
                                 'create_default_db.sh')
    ctx.download_resource(source=ps_config_source,
                          destination=ps_config_destination)
    utils.chmod('+x', ps_config_destination)
    # TODO: Can't we use a rest call here? Is there such a thing?
    utils.sudo('su - postgres -c "{cmd} {db} {user} {password}"'
               .format(cmd=ps_config_destination, db=db_name,
                       user=username, password=password))


def _create_postgres_pass_file(host, db_name, username, password):
    pgpass_path = '/root/.pgpass'
    ctx.logger.info('Creating postgresql pgpass file: {0}'.format(
        pgpass_path))
    postgresql_default_port = 5432
    pgpass_content = '{host}:{port}:{db_name}:{user}:{password}'.format(
        host=host,
        port=postgresql_default_port,
        db_name=db_name,
        user=username,
        password=password
    )
    # .pgpass file used by mgmtworker in snapshot workflow,
    # and need to be under th home directory of the user who run the snapshot
    # (currently root)
    if os.path.isfile(pgpass_path):
        ctx.logger.debug('Deleting {0} file..'.format(
            pgpass_path
        ))
        os.remove(pgpass_path)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(pgpass_content)
        temp_file.flush()
        utils.chmod('0600', temp_file.name)
        utils.move(source=temp_file.name,
                   destination=pgpass_path,
                   rename_only=True)
        ctx.logger.debug('Postgresql pass file {0} created'.format(
            pgpass_path))


def main():
    db_name = ctx.node.properties['postgresql_db_name']
    host = ctx.node.properties['postgresql_host']
    _create_postgres_pass_file(host=host,
                               db_name='*',
                               username='cloudify',
                               password='cloudify')
    _start_postgres()
    _create_default_db(db_name=db_name,
                       username='cloudify',
                       password='cloudify')

    if utils.is_upgrade or utils.is_rollback:
        # restore the 'provider_context' and 'snapshot' elements from file
        # created in the 'create.py' script.
        ctx.logger.error('NOT IMPLEMENTED - need to restore upgrade data')


main()
