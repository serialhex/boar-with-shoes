# NOTES!!!!

rubypython 0.5.3 does not work in arch64, use this fix:
pythonexec.rb
24:    elsif @realname =~ /#{@version}$/
25:      @realname = "#{@python}"

implement:  i dunno
	class Repo:
		get_repo_path
		get_queue_path
		get_blob_path
		get_recipe_path
