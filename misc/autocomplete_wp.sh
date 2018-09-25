# ----------------------------------------------
# Bash autocomplete script for the WordPress CLI
# ----------------------------------------------
#
# For Bash users, source this file in your shell (e.g. ~/.bashrc)
# to enable autocompletion of "wp" commands.
#
_wp_cli()
{
	local cur prev
	
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case ${COMP_CWORD} in
		1)
			# top level commands here
			COMPREPLY=($(compgen -W "cache cap cli comment config core cron db embed eval eval-file export help i18n import language media menu network option package plugin post post-type rewrite role scaffold search-replace server shell sidebar site super-admin taxonomy term theme transient user widget --path=<path> --url=<url> --ssh=[<scheme>:][<user>@]<host|container>[:<port>][<path>] --http=<http> --user=<id|login|email> --skip-plugins[=<plugins>] --skip-themes[=<themes>] --skip-packages --require=<path> --no-color --color --debug[=<group>] --prompt[=<assoc>] --quiet" -- ${cur}))
			;;
		2)
			# second level commands, per top level command
			case ${prev} in
                'cache')
                    COMPREPLY=($(compgen -W "add decr delete flush get incr replace set type" -- ${cur}))
                    ;;
                'cap')
                    COMPREPLY=($(compgen -W "add list remove" -- ${cur}))
                    ;;
                'cli')
                    COMPREPLY=($(compgen -W "alias check-update cmd-dump completions has-command info param-dump update version" -- ${cur}))
                    ;;
                'comment')
                    COMPREPLY=($(compgen -W "approve count create delete exists generate get list meta recount spam status trash unapprove unspam untrash update" -- ${cur}))
                    ;;
                'config')
                    COMPREPLY=($(compgen -W "create delete edit get has list path set shuffle-salts" -- ${cur}))
                    ;;
                'core')
                    COMPREPLY=($(compgen -W "check-update download install is-installed multisite-convert multisite-install update update-db verify-checksums version" -- ${cur}))
                    ;;
                'cron')
                    COMPREPLY=($(compgen -W "event schedule test" -- ${cur}))
                    ;;
                'db')
                    COMPREPLY=($(compgen -W "check clean cli columns create drop export import optimize prefix query repair reset search size tables" -- ${cur}))
                    ;;
                'embed')
                    COMPREPLY=($(compgen -W "cache fetch handler provider" -- ${cur}))
                    ;;
                #'eval')
                #    COMPREPLY=($(compgen -W "" -- ${cur}))
                #    ;;
                #'eval-file')
                #    COMPREPLY=($(compgen -W "" -- ${cur}))
                #    ;;
                #'export')
                #    COMPREPLY=($(compgen -W "" -- ${cur}))
                #    ;;
                'help')
                    COMPREPLY=($(compgen -W "cache cap cli comment config core cron db embed eval eval-file export help i18n import language media menu network option package plugin post post-type rewrite role scaffold search-replace server shell sidebar site super-admin taxonomy term theme transient user widget" -- ${cur}))
                    ;;
                'i18n')
                    COMPREPLY=($(compgen -W "make-pot" -- ${cur}))
                    ;;
                #'import')
                #    COMPREPLY=($(compgen -W "" -- ${cur}))
                #    ;;
                'language')
                    COMPREPLY=($(compgen -W "core plugin theme" -- ${cur}))
                    ;;
                'media')
                    COMPREPLY=($(compgen -W "image-size import regenerate" -- ${cur}))
                    ;;
                'menu')
                    COMPREPLY=($(compgen -W "create delete item list location" -- ${cur}))
                    ;;
                'network')
                    COMPREPLY=($(compgen -W "meta" -- ${cur}))
                    ;;
                'option')
                    COMPREPLY=($(compgen -W "add delete get list patch pluck update" -- ${cur}))
                    ;;
                'package')
                    COMPREPLY=($(compgen -W "browse install list path uninstall update" -- ${cur}))
                    ;;
                'plugin')
                    COMPREPLY=($(compgen -W "activate deactivate delete get install is-active is-installed list path search status toggle uninstall update verify-checksums" -- ${cur}))
                    ;;
                'post')
                    COMPREPLY=($(compgen -W "create delete edit generate get list meta term update" -- ${cur}))
                    ;;
                'post-type')
                    COMPREPLY=($(compgen -W "get list" -- ${cur}))
                    ;;
                'rewrite')
                    COMPREPLY=($(compgen -W "flush list structure" -- ${cur}))
                    ;;
                'role')
                    COMPREPLY=($(compgen -W "create delete exists list reset" -- ${cur}))
                    ;;
                'scaffold')
                    COMPREPLY=($(compgen -W "_s block child-theme plugin plugin-tests post-type taxonomy theme-tests" -- ${cur}))
                    ;;
                #'search-replace')
                #    COMPREPLY=($(compgen -W "" -- ${cur}))
                #    ;;
                'server')
                    COMPREPLY=($(compgen -W "--host= --port= --docroot= --config=" -- ${cur}))
                    ;;
                'shell')
                    COMPREPLY=($(compgen -W "--basic" -- ${cur}))
                    ;;
                'sidebar')
                    COMPREPLY=($(compgen -W "list" -- ${cur}))
                    ;;
                'site')
                    COMPREPLY=($(compgen -W "activate archive create deactivate delete empty list mature meta option private public spam switch-language unarchive unmature unspam" -- ${cur}))
                    ;;
                'super-admin')
                    COMPREPLY=($(compgen -W "add list remove" -- ${cur}))
                    ;;
                'taxonomy')
                    COMPREPLY=($(compgen -W "get list" -- ${cur}))
                    ;;
                'term')
                    COMPREPLY=($(compgen -W "create delete generate get list meta recount update" -- ${cur}))
                    ;;
                'theme')
                    COMPREPLY=($(compgen -W "activate delete disable enable get install is-active is-installed list mod path search status update" -- ${cur}))
                    ;;
                'transient')
                    COMPREPLY=($(compgen -W "delete get set type" -- ${cur}))
                    ;;
                'user')
                    COMPREPLY=($(compgen -W "add-cap add-role check-password create delete generate get import-csv list list-caps meta remove-cap remove-role reset-password session set-role spam term unspam update" -- ${cur}))
                    ;;
                'widget')
                    COMPREPLY=($(compgen -W "add deactivate delete list move reset update" -- ${cur}))
                    ;;
			esac
			;;
		*)
			COMPREPLY=()
			;;
	esac
}
complete -F _wp_cli wp
