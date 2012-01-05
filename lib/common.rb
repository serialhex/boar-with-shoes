
module Common
  RubyPython.start(:python_exe => 'python2.7')
  def sys add
    dir = File.dirname(__FILE__)
    sys = RubyPython.import 'sys'
    sys.path.append File.join(dir, add)
  end
end
