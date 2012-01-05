
require 'rubypython'
require 'pry'
require 'green_shoes'

require_relative 'common'

class RepoWrap
  include Common

  def initialize repo, create = false
    sys 'boar'
    sys 'boar/blobrepo'
    pyrepo = RubyPython.import('repository')
    if create
      if Dir.exist? repo
        alert "can't make repo in exsisting directory"
        # pyrepo.create_repository(repo+"tmp")
        # Dir.open(repo+"tmp") { |dir|
        #   dir.each { |f|
        #     next if f == '.' or f == '..'
        #     File.rename f, repo + '/' + f
        #   }
        # }
        # Dir.rmdir repo+"tmp"
      else
        pyrepo.create_repository(repo)
      end
    end
    @repo = pyrepo.Repo.new repo
  end

  attr_reader :repo

  def method_missing m, *args, &block
    @repo.send m, *args, &block
    super
  end
end
