The default configuration set by `basicConfig()` logs messages to `stderr`, and cron interprets any output to the `stderr` filehandle as email-worthy; you are, after all, not redirecting it.

See the [`logging.basicConfig()` documentation](http://docs.python.org/2/library/logging.html#logging.basicConfig):

> Does basic configuration for the logging system by creating a `StreamHandler` with a default `Formatter` and adding it to the root logger,

and the [`StreamHandler` docs](http://docs.python.org/2/library/logging.handlers.html#logging.StreamHandler):

> If *stream* is specified, the instance will use it for logging output; otherwise, `sys.stderr` will be used.

The work-around is to not set up a stream handler, or pick a different stream, or to pick a filename to log to:

    logging.basicConfig(level=logging.DEBUG, filename='/some/file/to/log/to')

or

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

By logging to `stdout` you write logging information to the same output stream as `print()` does.

Another work-around is to redirect `stderr` to `stdout`:

    * * * * * ~/test.py >> ~/test.log 2&>1
