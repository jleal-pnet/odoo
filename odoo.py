#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################
#  This is a PoC  #
###################

import argparse
import os


# TODO: Add metavars, specify types, destination, defaults per section, etc.
def main():
    # ------------- #
    #  Main parser  #
    # ------------- #
    main_parser = argparse.ArgumentParser(prog='odoo', description='Odoo CLI')
    # ----------------- #
    #  Logging options  #
    # ----------------- #
    logging_parser = argparse.ArgumentParser(add_help=False)
    logging_parser.add_argument(
        '-lf', '--logfile', nargs=1,
        help="path where the log file should be saved"
    )
    logging_parser.add_argument(
        '-sl', '--syslog', action='store_true',
        help="save odoo logs as system logs"
    )
    logging_parser.add_argument(
        '-L', '--log-level', help="which type of logs to display to stdin"
    )
    # ---------------- #
    #  Common options  #
    # ---------------- #
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '-ap', '--addons-path', nargs='+',
        help="space-separated list of paths to check for addons"
    )
    common_parser.add_argument(
        '-dd', '--data-dir', nargs=1,
        help="path to a directory where odoo-generated files should be stored"
    )
    # ------------ #
    #  Subparsers  #
    # ------------ #
    top_level_subparsers = main_parser.add_subparsers(help='sub-command help')
    dbname_parser = argparse.ArgumentParser(add_help=False)
    dbname_parser.add_argument(
        'dbname', nargs=1, help="name of the database"
    )
    # ------------- #
    #  DB creation  #
    # ------------- #
    create_parser = top_level_subparsers.add_parser(
        'create',
        help="create odoo databases",
        parents=[dbname_parser, logging_parser, common_parser]
    )
    create_parser.add_argument(
        '-d', '--demo', action='store_true',
        help="if specified demo data will be installed in the database"
    )
    create_parser.add_argument(
        '-l', '--launch', action='store_true',
        help="if specified, the db will be launched after db creation"
    )
    # ---------------- #
    #  DB duplication  #
    # ---------------- #
    dupe_parser = top_level_subparsers.add_parser(
        'duplicate',
        help="duplicate odoo databases",
    )
    dupe_parser.add_argument(
        'db_src', nargs=1, help="name of the source database"
    )
    dupe_parser.add_argument(
        'db_dest', nargs=1, help="name of the destination database"
    )
    # --------- #
    #  DB dump  #
    # --------- #
    dump_parser = top_level_subparsers.add_parser(
        'dump',
        help="dump odoo databases",
        parents=[dbname_parser, logging_parser]
    )
    dump_parser.add_argument(
        'filepath', nargs=1, help="path where the dump should be stored"
    )
    dump_parser.add_argument(
        '-f', '--format', choices=['gzip', 'raw', 'sql'],
        help="one of three available formats for the dump file"
    )
    # ------------ #
    #  DB restore  #
    # ------------ #
    restore_parser = top_level_subparsers.add_parser(
        'restore',
        help="restore odoo databases",
        parents=[dbname_parser, logging_parser]
    )
    restore_parser.add_argument(
        'filepath', nargs=1, help="path of the dump to restore"
    )
    restore_parser.add_argument(
        '--dbuuid', nargs=1, help="dbuuid of the db to restore"
    )
    # -------------- #
    #  Cron Process  #
    # -------------- #
    cron_parser = top_level_subparsers.add_parser(
        'cron',
        help="launch a cron thread for managing all databases' cron jobs"
    )
    cron_parser.add_argument(
        '-w', '--workers', nargs=1,
        help="amount of workers to assign to this cron thread"
    )
    cron_parser.add_argument(
        '-p', '--pid', nargs=1, help="pid for the cron thread"
    )
    # TODO: not one, but different --limit-* commands, maybe make a parser
    # and inherit in subparsers
    cron_parser.add_argument(
        '-l', '--limits', help="???"
    )
    # ------------ #
    #  Migrations  #
    # ------------ #
    migration_parser = top_level_subparsers.add_parser(
        'migrate',
        help="migrate the specified odoo database",
        parents=[dbname_parser, logging_parser]
    )
    migration_parser.add_argument(
        'spath', nargs=1,
        help="path to the migration scripts for the specified database"
    )
    # --------- #
    #  Imports  #
    # --------- #
    import_parser = top_level_subparsers.add_parser(
        'import',
        help="import csv data into odoo",
        parents=[dbname_parser, logging_parser, common_parser]
    )
    import_parser.add_argument(
        'filepath', nargs=1,
        help="path to the csv file to import into the odoo database"
    )
    import_parser.add_argument(
        '-p', '--import-partial', action='store_true',
        help="import in small batches instead of one big batch"
    )
    # --------------------- #
    #  Module installation  #
    # --------------------- #
    install_parser = top_level_subparsers.add_parser(
        'install',
        help="install odoo modules",
        parents=[dbname_parser, logging_parser, common_parser]
    )
    install_parser.add_argument(
        'modules', nargs='+',
        help="space-separated list of modules to be installed"
    )
    # ---------------- #
    #  Module updates  #
    # ---------------- #
    update_parser = top_level_subparsers.add_parser(
        'update',
        help="update odoo modules",
        parents=[dbname_parser, logging_parser, common_parser]
    )
    update_parser.add_argument(
        'modules', nargs='+',
        help="space-separated list of modules to be updated"
    )
    # --------------------------- #
    #  Standalone test execution  #
    # --------------------------- #
    test_parser = top_level_subparsers.add_parser(
        'test', help="execute specific unit/integration tests",
        parents=[logging_parser, common_parser]
    )
    test_parser.add_argument(
        'tag', nargs='*', help="only run tests with the specified tags"
    )
    test_parser.add_argument(
        '-pp', '--pretty-print', action='store_true',
        help="print the test results in a pretty format"
    )
    test_parser.add_argument(
        '-e', '--exclude', nargs='+',
        help="exclude tests with these tags when running the tests suite"
    )
    test_parser.add_argument(
        '-ff', '--fail-fast', action='store_true',
        help="terminate the test execution upon first failure"
    )
    test_parser.add_argument(
        '-s', '--save', nargs='*',
        help="save the test results to the specified file or current directory"
    )
    # -------------- #
    #  Translations  #
    # -------------- #
    translation_parser = top_level_subparsers.add_parser(
        'translate', help="tools for handling translations in odoo",
        parents=[dbname_parser, logging_parser, common_parser]
    )
    translation_subparsers = translation_parser.add_subparsers(
        help='translation toolset help'
    )
    # Load subcommand
    t_load_parser = translation_subparsers.add_parser(
        'load', help="load a translation into the specified database"
    )
    t_load_parser.add_argument(
        'language', nargs=1, help="language to be loaded"
    )
    # Import subcommand
    t_import_parser = translation_subparsers.add_parser(
        'import', help="import translations"
    )
    t_import_parser.add_argument(
        'language', nargs=1,
        help="language for which translations will be imported"
    )
    t_import_parser.add_argument(
        'infile', nargs=1,
        help="path to the PO/CSV file containing the translations"
    )
    t_import_parser.add_argument(
        '-o', '--overwrite', action='store_true',
        help="if specified, translations in the database will be overwritten "
        "for those found in the input file"
    )
    # Export subcommand
    t_export_parser = translation_subparsers.add_parser(
        'export', help="export translations"
    )
    t_export_parser.add_argument(
        'language', nargs=1,
        help="language for which translations will be exported"
    )
    t_export_parser.add_argument(
        'outfile', nargs=1,
        help="path to where the exported records will be stored"
    )
    t_export_parser.add_argument(
        '-t', '--template', help="???"
    )
    # ------- #
    #  Serve  #
    # ------- #
    serve_parser = top_level_subparsers.add_parser(
        'serve',
        parents=[common_parser, logging_parser],
        help="launch an odoo server"
    )
    serve_parser.add_argument(
        '-i', '--init', nargs='+',
        help="space-separated list of modules to install during server launch"
    )
    serve_parser.add_argument(
        '-u', '--update', nargs='+',
        help="space-separated list of modules to update during server launch"
    )
    serve_parser.add_argument(
        '-l', '--load', nargs='+',
        help="space-separated list of server-wide modules"
    )
    serve_parser.add_argument(
        '--interface-address', nargs=1,
        help="IPv4 address for the HTTP/XMLRPC interface"
    )
    serve_parser.add_argument(
        '--proxy-mode', action='store_true',
        help="something something reverse proxy"
    )
    serve_parser.add_argument(
        '-p', '--port', nargs=1,
        help="HTTP port for the server"
    )
    serve_parser.add_argument(
        '--longpolling-port', nargs=1,
        help="longpolling port for the server"
    )
    serve_parser.add_argument(
        '-d', '--database', nargs=1,
        help="database to select or create if it doesn't exist"
    )
    serve_parser.add_argument(
        '--db-filter', nargs=1,
        help="databases to make available"
    )
    serve_parser.add_argument(
        '--no-database-list', action='store_true',
        help="don't show list of databases through Web UI"
    )
    serve_parser.add_argument(
        '--dev', nargs='+',
        choices=[
            # TODO: Re-parse this later on and remove duplicates
            'pudb', 'wdb', 'ipdb', 'pdb', 'all', 'reload', 'qweb',
            'werkzeug', 'xml'
        ],
        help="enable developer mode"
    )
    serve_parser.add_argument(
        '--without-demo', action='store_true',
        help="disable loading demo data for modules to be installed"
    )
    serve_parser.add_argument(
        '--pid-file', nargs=1,
        help="file where the server pid will be stored"
    )
    # Advanced options
    serve_parser.add_argument(
        '--limit-virt-count', nargs=1,
        help="Force a limit on the maximum number of records kept in the "
        "virtual osv_memory tables. The default is False, which means no "
        "count-based limit."
    )
    serve_parser.add_argument(
        '--limit-virt-age', nargs=1,
        help="Force a limit on the maximum age of records kept in the "
        "virtual osv_memory tables. This is a decimal value expressed in "
        "hours, the default is 1 hours."
    )
    serve_parser.add_argument(
        '--max-cron-threads', nargs=1,
        help="Maximum number of threads processing concurrently cron jobs "
        "(default 2)."
    )
    # Multi-processing, POSIX only
    if os.name == 'posix':
        serve_parser.add_argument(
            '--workers', nargs=1,
            help="Specify the number of workers, 0 disable prefork mode."
        )
        # Different limits
        serve_parser.add_argument(
            '--limit-memory-soft', nargs=1,
            help="Maximum allowed virtual memory per worker, when reached the "
            "worker will be reset after the current request (default 640MiB)"
        )
        serve_parser.add_argument(
            '--limit-memory-hard', nargs=1,
            help="Maximum allowed virtual memory per worker, when reached, "
            "memory allocation will fail (default 768MiB)"
        )
        serve_parser.add_argument(
            '--limit-time-cpu', nargs=1,
            help="Maximum allowed CPU time per request (default 60)"
        )
        serve_parser.add_argument(
            '--limit-time-real', nargs=1,
            help="Maximum allowed real time per request (default 120)"
        )
        serve_parser.add_argument(
            '--limit-time-real-cron', nargs=1,
            help="Maximum allowed real time per cron job "
            "(default --limit-time-real), set to 0 for no limit"
        )
        serve_parser.add_argument(
            '--limit-request', nargs=1,
            help="Maximum number of request to be processed per worker "
            "(default 8192)"
        )
    # --------------- #
    #  Configuration  #
    # --------------- #
    config_parser = top_level_subparsers.add_parser(
        'config',
        help="set up your Odoo configuration"
    )
    config_parser.add_argument(
        'setting', nargs=1,
        help="setting to modify"
    )
    # Just to avoid any shenanigans
    ex_group = config_parser.add_mutually_exclusive_group()
    ex_group.add_argument(
        'new_val', nargs='?', default=None,
        help="new value for the specified setting"
    )
    ex_group.add_argument(
        '-e', '--edit', action='store_true',
        help="open the settings file with the preferred text editor"
    )
    # ------------ #
    #  Deployment  #
    # ------------ #
    deploy_parser = top_level_subparsers.add_parser(
        'deploy',
        help="deploy a module on an Odoo instance"
    )
    deploy_parser.add_argument(
        'path', nargs=1,
        help="path of the module to be deployed"
    )
    deploy_parser.add_argument(
        'url', nargs='?',
        help="url of the server",
        default="http://localhost:8069"
    )
    # ---------- #
    #  Scaffold  #
    # ---------- #
    scaffold_parser = top_level_subparsers.add_parser(
        'scaffold',
        help="create an empty module following a template"
    )
    scaffold_parser.add_argument(
        'name', nargs=1,
        help="name of the module to create"
    )
    scaffold_parser.add_argument(
        'dest', nargs='?', default='.',
        help="directory where the newly-created module will be stored "
        "(default is current working directory)"
    )
    scaffold_parser.add_argument(
        '-t', '--template', nargs=1,
        help="provide a template for the module to be generated"
    )
    # ----------------- #
    #  Shell Interface  #
    # ----------------- #
    shell_parser = top_level_subparsers.add_parser(
        'shell',
        help="activate the shell interface for the specified database",
        parents=[common_parser, logging_parser]
    )
    shell_parser.add_argument(
        '-d', '--database',
        help="a database to run the shell on, creates a new one by default"
    )
    shell_parser.add_argument(
        '-r', '--repl', choices=['python', 'ipython', 'ptpython'],
        help="the repl to be used for the shell session"
    )

    # Parse them args
    parsed = main_parser.parse_args()
    print(parsed)


if __name__ == '__main__':
    main()
