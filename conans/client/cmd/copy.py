from conans.model.ref import PackageReference, ConanFileReference
import os
from conans.util.files import rmdir
import shutil
from conans.errors import ConanException
from conans.client.loader_parse import load_conanfile_class
from conans.client.source import complete_recipe_sources


def _prepare_sources(client_cache, reference, remote_manager, registry):
    conan_file_path = client_cache.conanfile(reference)
    conanfile = load_conanfile_class(conan_file_path)
    complete_recipe_sources(remote_manager, client_cache, registry,
                            conanfile, reference)
    return conanfile.short_paths


def _get_package_ids(client_cache, reference, package_ids):
    if not package_ids:
        return []
    if package_ids is True:
        packages = client_cache.packages(reference)
        if os.path.exists(packages):
            package_ids = os.listdir(packages)
        else:
            package_ids = []
    return package_ids


def cmd_copy(reference, user_channel, package_ids, client_cache, user_io, remote_manager,
             registry, force=False):
    """
    param package_ids: Falsey=do not copy binaries. True=All existing. []=list of ids
    """
    src_ref = ConanFileReference.loads(reference)

    short_paths = _prepare_sources(client_cache, src_ref, remote_manager, registry)
    package_ids = _get_package_ids(client_cache, src_ref, package_ids)
    package_copy(src_ref, user_channel, package_ids, client_cache, user_io,
                 short_paths, force)


def package_copy(src_ref, user_channel, package_ids, paths, user_io,
                 short_paths=False, force=False):
    dest_ref = ConanFileReference.loads("%s/%s@%s" % (src_ref.name,
                                                      src_ref.version,
                                                      user_channel))
    # Copy export
    export_origin = paths.export(src_ref)
    if not os.path.exists(export_origin):
        raise ConanException("'%s' doesn't exist" % str(src_ref))
    export_dest = paths.export(dest_ref)
    if os.path.exists(export_dest):
        if not force and not user_io.request_boolean("'%s' already exist. Override?"
                                                     % str(dest_ref)):
            return
        rmdir(export_dest)
    shutil.copytree(export_origin, export_dest, symlinks=True)
    user_io.out.info("Copied %s to %s" % (str(src_ref), str(dest_ref)))

    export_sources_origin = paths.export_sources(src_ref, short_paths)
    export_sources_dest = paths.export_sources(dest_ref, short_paths)
    if os.path.exists(export_sources_dest):
        rmdir(export_sources_dest)
    shutil.copytree(export_sources_origin, export_sources_dest, symlinks=True)
    user_io.out.info("Copied sources %s to %s" % (str(src_ref), str(dest_ref)))

    # Copy packages
    for package_id in package_ids:
        package_origin = PackageReference(src_ref, package_id)
        package_dest = PackageReference(dest_ref, package_id)
        package_path_origin = paths.package(package_origin, short_paths)
        package_path_dest = paths.package(package_dest, short_paths)
        if os.path.exists(package_path_dest):
            if not force and not user_io.request_boolean("Package '%s' already exist."
                                                         " Override?" % str(package_id)):
                continue
            rmdir(package_path_dest)
        shutil.copytree(package_path_origin, package_path_dest, symlinks=True)
        user_io.out.info("Copied %s to %s" % (str(package_id), str(dest_ref)))
