def getch(prompt=None):
    """Gets a single character from standard input.  Does not echo to the screen."""
    import sys
    
    if not hasattr(getch, '_impl'):
        try:
            msvcrt = __import__('msvcrt')
            impl = msvcrt.getch
        except ImportError:
            def getch_unix():
                termios = __import__('termios')
                tty = __import__('tty')
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return ch
            impl = getch_unix
        setattr(getch, '_impl', impl)
    
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    ch = getch._impl()
    
    if ord(ch) == 3:
        raise KeyboardInterrupt
    
    if ord(ch) == 4:
        raise EOFError
    
    if prompt:
        sys.stdout.write('\n')
        sys.stdout.flush()
    
    return ch
