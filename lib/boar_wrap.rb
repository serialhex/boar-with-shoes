
# this is the boar wrapper class
# it has become a class...  because they're cooler

require 'rubypython'
require 'pry'

class BoarWrap
  def initialize repo, create = false
    run_python repo
    binding.pry
  end

  def run_python method, *args, &block
    dir = File.dirname(__FILE__)
    # change hardcoded python2.7
    RubyPython.run(:python_exe => 'python2.7') do
      sys = RubyPython.import 'sys'
      sys.path.append File.join(dir, 'boar')
      sys.path.append File.join(dir, 'boar/blobrepo')
      pyrepo = RubyPython.import('repository')
      pyrepo.create_repository(repo) if create
      @repo = pyrepo.Repo.new repo
      pyfront = RubyPython.import('front')
      @front = pyfront.Front.new(@repo)
    end
  end
end


if __FILE__ == $0
  foo = BoarWrap.new "/home/serialhex/src/boar_with_sneakers/test/foo", false
end
