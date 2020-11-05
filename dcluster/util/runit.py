import logging
import os
import shlex
import subprocess
import threading


def listen_and_log(process, stream_name, logger, log_level, with_print, stream_outputs):

    stream = getattr(process, stream_name)

    stream_lines = []
    while True:
        # try to read the stream
        # this will consume the stream data, so we save it in stream_lines
        # this call will block the current thread
        rc = process.poll()
        output_line = stream.readline()
        if not output_line and rc is not None:
            # poll returns None while the process is running
            # if we are here, there is no more output and the process has returned a code

            # save the return code, we might not be able to retrieve it later
            # https://stackoverflow.com/questions/48910693/python-subprocess-returns-wrong-exit-code
            # this still fails about 5% of the time on Python 2.7...
            stream_outputs['rc'] = rc
            break

        if output_line:
            # save stdout data
            stream_lines.append(output_line)

            if logger:
                logger.log(log_level, output_line.rstrip())
            if with_print:
                print(output_line.rstrip())

    # store the output
    stream_outputs[stream_name] = ''.join(stream_lines)


def execute(call_string, logger=None, log_level=None, cwd=None, with_shlex=False,
            env=os.environ.copy(), with_print=False):

    # execute the process inside a shell, keep shell environment
    if with_shlex:
        with_shell = False
        call_string = shlex.split(call_string)
        print(call_string)
    else:
        with_shell = True

    if log_level is None:
        log_level = logging.WARN

    stream_outputs = {}

    process = subprocess.Popen(call_string, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=with_shell, cwd=cwd,
                               universal_newlines=True, env=env)

    stdout_args = (process, 'stdout', logger, log_level, with_print, stream_outputs)
    stdout_thread = threading.Thread(target=listen_and_log, name='Stdout', args=stdout_args)

    stderr_args = (process, 'stderr', logger, log_level, with_print, stream_outputs)
    stderr_thread = threading.Thread(target=listen_and_log, name='Stderr', args=stderr_args)

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()

    # if we call process.poll() to retrieve the returncode, it might be too late
    # the child may already be dead, and the poll will return '0' even if there was an error
    return (stream_outputs['stdout'], stream_outputs['stderr'], stream_outputs['rc'])


if __name__ == '__main__':

    log_level = logging.WARN
    logging.basicConfig(level=log_level, format='(%(threadName)-10s) [%(levelname)s] %(message)s',)

    stdout_text = 'This is nice output'
    stderr_text = 'Wrote to stderr'
    (stdout, stderr, rc) = execute('/bin/echo %s && >&2 /bin/echo %s' % (stdout_text, stderr_text),
                                   logger=logging, log_level=log_level)
