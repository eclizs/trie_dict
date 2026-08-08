#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include "trie.h"

static void expect_true(bool condition, const char *message)
{
    if (!condition)
    {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(EXIT_FAILURE);
    }
}

static void assert_word_list_contains(WordList list, const char *expected_word)
{
    bool found = false;

    expect_true(list.count > 0, "word list should not be empty");

    for (int i = 0; i < list.count; i++)
    {
        if (strcmp(list.entries[i], expected_word) == 0)
        {
            found = true;
            break;
        }
    }

    expect_true(found, "expected word was not returned");
}

static void test_insert_find_and_delete(void)
{
    TrieNode *root = NULL;
    char word[] = "Hello";
    char prefix[] = "h";
    char delete_word[] = "Hello";

    int result = insertTrieNode(&root, word);
    expect_true(result == 201, "insert should return 201 for a new word");
    expect_true(root != NULL, "root trie should be initialized");

    TrieNode *node = findPrefixNode(root, word);
    expect_true(node != NULL, "findPrefixNode should resolve the inserted word");
    expect_true(node->terminal, "resolved node should be terminal");

    WordList found = findWords(root, prefix);
    expect_true(found.count == 1, "prefix search should return exactly one match");
    assert_word_list_contains(found, "Hello");
    freeWordList(found);

    expect_true(deleteWord(&root, delete_word), "deleteWord should remove the inserted word");

    WordList empty = findWords(root, prefix);
    expect_true(empty.count == 0, "deleted word should no longer be returned");
    freeWordList(empty);

    destroyTrieNode(&root);
}

static void test_duplicate_insert(void)
{
    TrieNode *root = NULL;
    char first_word[] = "hello";
    char prefix[] = "hello";

    int first = insertTrieNode(&root, first_word);
    int second = insertTrieNode(&root, first_word);

    expect_true(first == 201, "first insert should create a new word");
    expect_true(second == 409, "second insert should fail");

    WordList found = findWords(root, prefix);
    expect_true(found.count == 1, "duplicate insert should not create a second entry");
    expect_true(strcmp(found.entries[0], "hello") == 0, "original word should be retained");

    freeWordList(found);
    destroyTrieNode(&root);
}

static void test_invalid_and_empty_inputs(void)
{
    TrieNode *root = NULL;
    char invalid_word[] = "bad:word";
    char empty_word[] = "";
    char prefix[] = "";

    int invalid_insert = insertTrieNode(&root, invalid_word);
    expect_true(invalid_insert == 422, "insert should reject unsupported characters");

    int empty_error = insertTrieNode(&root, empty_word);
    expect_true(empty_error == 400, "insert should reject empty words");

    WordList empty = findWords(root, prefix);
    expect_true(empty.count == 0, "findWords should return no entries for an empty trie");
    freeWordList(empty);

    destroyTrieNode(&root);
}

int main(void)
{
    test_insert_find_and_delete();
    test_duplicate_insert();
    test_invalid_and_empty_inputs();

    puts("All trie tests passed.");
    return EXIT_SUCCESS;
}
